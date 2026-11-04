"""Resumable two-state DFT oxygen screening; real runs require explicit CLI."""
import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'dft'))
from dft import embed, optimize
from run_set import _done
from o2_calibration import classify

OUT = ROOT / 'dft/runs/funnel_tier1'
COMMON = ROOT / 'dft/runs/ref_set/_common.json'
CALIB = ROOT / 'dft/runs/ref_set/o2_calib.json'


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
    os.replace(tmp, path)


def load_calibration(path, no_calib=False):
    if no_calib:
        return None
    if not Path(path).exists():
        raise FileNotFoundError(f'O2 calibration missing: {path}; use --no-calib only for tests')
    calib = json.loads(Path(path).read_text())
    for category in ('carbocyclic', 'heterocyclic'):
        if not math.isfinite(float(calib[category]['mean_shift'])):
            raise ValueError('Invalid calibration')
    return calib


def gate(smiles, e2, oxygen, calib, tol=0.):
    raw = oxygen - e2
    category = classify(smiles) if calib is not None else None
    corrected = raw + float(calib[category]['mean_shift']) if calib is not None else raw
    return {'raw_margin': raw, 'calibrated_margin': corrected, 'o2_class': category, 'survives': corrected >= .15 - tol}


def run_molecule(item, out, gpu, optimize_fn=optimize):
    path = Path(out) / (item['inchikey'] + '.json')
    data = json.loads(path.read_text()) if path.exists() else {'smiles': item['smiles'], 'inchikey': item['inchikey'], 'states': {}}
    if data['smiles'] != item['smiles'] or data['inchikey'] != item['inchikey']:
        raise ValueError('Molecule differs from existing checkpoint')
    symbols, coords = embed(item['smiles'])
    for name, charge, spin in [('Q_radical_anion', -1, 1), ('Q_dianion', -2, 0)]:
        if not _done(data['states'].get(name)):
            data['states'][name] = optimize_fn(symbols, coords, charge, spin, gpu=gpu)
            atomic_json(path, data)
    return data


def _worker(gpu, items, out):
    os.environ['CUDA_VISIBLE_DEVICES'] = gpu
    for item in items:
        run_molecule(item, out, True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--library', type=Path, default=Path(__file__).with_name('tier1_subset.csv'))
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--calib', type=Path, default=CALIB)
    p.add_argument('--no-calib', action='store_true')
    p.add_argument('--limit', type=int)
    p.add_argument('--gpus', default='0,1')
    p.add_argument('--tol', type=float, default=0.)
    args = p.parse_args()
    calib = load_calibration(args.calib, args.no_calib)
    if not 0 <= args.tol <= .15:
        p.error('tol must be between 0 and .15')
    common = json.loads(COMMON.read_text())['states']
    if not all(_done(common.get(x)) for x in ('O2', 'O2_radical_anion')):
        raise ValueError('O2 reference states are incomplete')
    oxygen = (common['O2_radical_anion']['energy'] - common['O2']['energy']) * 27.2114
    with args.library.open() as f:
        items = list(csv.DictReader(f))[:args.limit]
    if len({i['inchikey'] for i in items}) != len(items):
        raise ValueError('duplicate library keys')
    gpus = [x.strip() for x in args.gpus.split(',') if x.strip()]
    if not gpus: p.error('at least one GPU required')
    args.out.mkdir(parents=True, exist_ok=True)
    with mp.get_context('spawn').Pool(len(gpus)) as pool:
        pool.starmap(_worker, [(gpu, items[i::len(gpus)], args.out) for i, gpu in enumerate(gpus)])
    rows = []
    for item in items:
        data = json.loads((args.out / (item['inchikey'] + '.json')).read_text())
        states = data['states']
        if not all(_done(states.get(n)) for n in ('Q_radical_anion', 'Q_dianion')): continue
        e2 = (states['Q_dianion']['energy'] - states['Q_radical_anion']['energy']) * 27.2114
        rows.append({**item, 'E2_eV': e2, **gate(item['smiles'], e2, oxygen, calib, args.tol)})
    with (args.out / 'tier1.csv').open('w', newline='') as f:
        fields = list(items[0]) if items else ['smiles', 'inchikey', 'core', 'substituents', 'sa_score']
        fields += [name for name in ('E2_eV', 'raw_margin', 'calibrated_margin', 'o2_class', 'survives') if name not in fields]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    csvpath = args.out / 'tier1.csv'
    meta = {'csv_sha256': hashlib.sha256(csvpath.read_bytes()).hexdigest(),
            'common_sha256': hashlib.sha256(COMMON.read_bytes()).hexdigest(),
            'calibration_sha256': hashlib.sha256(args.calib.read_bytes()).hexdigest() if calib is not None else None,
            'tolerance': args.tol}
    atomic_json(args.out / 'tier1.csv.meta.json', meta)
    print(f"Completed {len(rows)}/{len(items)}; gate passed {sum(r['survives'] for r in rows)}")

if __name__ == '__main__': main()
