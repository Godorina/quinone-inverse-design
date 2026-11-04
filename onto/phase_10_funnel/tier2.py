"""Persisted diverse UCB rounds; invoking the CLI starts full GPU DFT."""
import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
import os
import random
import sys
from pathlib import Path

from tier1 import ROOT, COMMON, CALIB, atomic_json, load_calibration
import surrogate
sys.path.insert(0, str(ROOT / 'dft'))
from run_set import run_molecule, run_selected, summarize
from closed_loop import score

OUT = ROOT / 'dft/runs/funnel_tier2'


def read_ledger(path):
    path = Path(path)
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def append_ledger(path, row):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    rows = read_ledger(path)
    old = next((r for r in rows if r['inchikey'] == row['inchikey']), None)
    if old:
        if old != row: raise ValueError('Conflicting ledger entry')
        return
    # Atomic replacement avoids a partial JSONL record after interruption.
    temp = path.with_suffix('.tmp')
    temp.write_text(''.join(json.dumps(r, sort_keys=True, allow_nan=False) + '\n' for r in rows + [row]))
    os.replace(temp, path)


def _worker(gpu, items, out):
    os.environ['CUDA_VISIBLE_DEVICES'] = gpu
    for item in items: run_molecule(item, out, True)


def execute_round(selected, out, ledgerpath, n, line, calib, dispatch, summarize_fn=summarize):
    """Evaluate only unfinished selections and commit each completed result once."""
    done = {row['inchikey'] for row in read_ledger(ledgerpath)}
    pending = [item for item in selected if item['inchikey'] not in done]
    if pending:
        dispatch(pending)
        summary = summarize_fn(out)
        by_key = {item['inchikey']: item for item in pending}
        for row in summary['molecules']:
            if row['inchikey'] not in by_key:
                continue
            item = by_key[row['inchikey']]
            scored = score({**row, 'smiles': item['smiles']}, line, calib)
            append_ledger(ledgerpath, {'round': n, **scored})
    completed = {row['inchikey'] for row in read_ledger(ledgerpath)}
    return all(item['inchikey'] in completed for item in selected)


def run_candidate_file(args, calib, gpus):
    """Run a saved MLP selection directly, without a second surrogate selection."""
    with args.candidates.open() as handle:
        selected = list(csv.DictReader(handle))
    if not selected or len({r['inchikey'] for r in selected}) != len(selected):
        raise ValueError('Candidate CSV must contain unique molecules')
    from generate import _inchikey
    if any(_inchikey(r['smiles']) != r['inchikey'] for r in selected):
        raise ValueError('Candidate SMILES/InChIKey mismatch')
    linepath = ROOT / 'dft/runs/ref_set/lines.json'
    line = json.loads(linepath.read_text())['v2']
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    config = {'mode': 'direct_candidates', 'candidates': digest(args.candidates),
              'common': digest(COMMON), 'line': digest(linepath),
              'calib': digest(args.calib) if calib is not None else None}
    args.out.mkdir(parents=True, exist_ok=True)
    configpath = args.out / 'config.json'
    if configpath.exists() and json.loads(configpath.read_text()) != config:
        raise ValueError('Run settings changed; use a new output directory')
    if not configpath.exists(): atomic_json(configpath, config)
    out = args.out / 'round_1'; out.mkdir(exist_ok=True)
    manifest = out / 'selection.json'
    if not manifest.exists(): atomic_json(manifest, {'round': 1, 'selected': selected, 'mode': 'direct_candidates'})
    def dispatch(pending):
        run_selected([], out, True, common_path=COMMON)
        with mp.get_context('spawn').Pool(len(gpus)) as pool:
            pool.starmap(_worker, [(gpu, pending[i::len(gpus)], out) for i, gpu in enumerate(gpus)])
    complete = execute_round(selected, out, args.out / 'ledger.jsonl', 1, line, calib, dispatch)
    print(f'Direct candidate run: {len(selected)} selected; complete={complete}')
    return complete


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tier1', type=Path, default=ROOT / 'dft/runs/funnel_tier1/tier1.csv')
    p.add_argument('--candidates', type=Path, help='Run this saved candidate CSV directly')
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--calib', type=Path, default=CALIB)
    p.add_argument('--no-calib', action='store_true')
    p.add_argument('--rounds', type=int, default=3); p.add_argument('--batch', type=int, default=5)
    p.add_argument('--gpus', default='0,1'); p.add_argument('--kappa', type=float, default=2.)
    p.add_argument('--seed', type=int, default=0)
    args = p.parse_args()
    calib = load_calibration(args.calib, args.no_calib)
    if args.rounds < 1 or args.batch < 1: p.error('rounds and batch must be positive')
    gpus = [g.strip() for g in args.gpus.split(',') if g.strip()]
    if not gpus: p.error('at least one GPU required')
    if args.candidates:
        run_candidate_file(args, calib, gpus)
        return
    meta = json.loads(Path(str(args.tier1) + '.meta.json').read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    expected = {'csv_sha256': sha(args.tier1), 'common_sha256': sha(COMMON),
                'calibration_sha256': sha(args.calib) if calib is not None else None}
    if any(meta.get(k) != v for k, v in expected.items()):
        raise ValueError('Tier-1 CSV, O2 reference, or calibration changed; regenerate tier 1')
    with args.tier1.open() as f: survivors = [r for r in csv.DictReader(f) if r['survives'].lower() == 'true']
    linepath = ROOT / 'dft/runs/ref_set/lines.json'
    line = json.loads(linepath.read_text())['v2']
    def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    config = {'tier1': digest(args.tier1), 'common': digest(COMMON), 'line': digest(linepath), 'calib': digest(args.calib) if calib else None, 'batch': args.batch, 'kappa': args.kappa, 'seed': args.seed}
    args.out.mkdir(parents=True, exist_ok=True)
    configpath = args.out / 'config.json'
    if configpath.exists() and json.loads(configpath.read_text()) != config: raise ValueError('Run settings changed; use a new output directory')
    if not configpath.exists(): atomic_json(configpath, config)
    ledgerpath = args.out / 'ledger.jsonl'
    for n in range(1, args.rounds + 1):
        out = args.out / f'round_{n}'; out.mkdir(exist_ok=True)
        manifestpath = out / 'selection.json'
        ledger = read_ledger(ledgerpath)
        if manifestpath.exists():
            manifest = json.loads(manifestpath.read_text())
        else:
            used = {r['inchikey'] for r in ledger}
            candidates = [r for r in survivors if r['inchikey'] not in used]
            if not candidates: break
            train = surrogate.training_rows(ledger)
            if not train: raise ValueError('No full-DFT training rows')
            model = surrogate.GP([r['smiles'] for r in train], [r['f'] for r in train])
            smiles = [r['smiles'] for r in candidates]; mean, std = model.predict(smiles)
            picked = surrogate.select(smiles, mean, std, args.batch, args.kappa)
            order = list(range(len(candidates))); random.Random(args.seed + n).shuffle(order)
            baseline = surrogate.select(smiles, mean, std, args.batch, order=order)
            manifest = {'round': n, 'selected': [{**candidates[i], 'predicted_f': float(mean[i]), 'predicted_std': float(std[i])} for i in picked], 'random_baseline': [candidates[i]['inchikey'] for i in baseline], 'seed': args.seed + n}
            atomic_json(manifestpath, manifest)
        selected = manifest['selected']
        if not selected: break
        def dispatch(pending):
            run_selected([], out, True, common_path=COMMON)
            with mp.get_context('spawn').Pool(len(gpus)) as pool:
                pool.starmap(_worker, [(gpu, pending[i::len(gpus)], out) for i, gpu in enumerate(gpus)])
        if not execute_round(selected, out, ledgerpath, n, line, calib, dispatch):
            print(f'Round {n}: incomplete result; stopped for retry'); break
        print(f'Round {n}: {len(selected)} complete; random baseline in selection.json')

if __name__ == '__main__': main()
