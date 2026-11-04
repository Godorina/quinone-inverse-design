"""CPU-only GP screening against existing DFT labels; no DFT or MLIP runs."""
import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

from rdkit import Chem
from mlp_screen import (ROOT, LIBRARY, CANDIDATES, COMMON, CALIB, _done, _inchikey,
                        training_records, gp_e2, pick_candidates, oxygen_plausible,
                        classify, load_calibration, atomic_json, sha)


def unsupported(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 'invalid_smiles'
    # ponytail: DFT feasibility only; the enumerated library already applies design rules.
    bad = sorted({a.GetSymbol() for a in mol.GetAtoms()} - {'C', 'H', 'N', 'O', 'F', 'Cl', 'Br', 'S'})
    return 'unsupported_element:' + ','.join(bad) if bad else None


def computed_keys(records):
    keys = {r['inchikey'] for r in records}
    pattern = re.compile(r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$')
    # Include DFT checkpoints without complete training labels, but never MLIP files.
    for path in sorted((ROOT / 'dft/runs').glob('**/*.json')):
        if 'funnel_mlp' in path.parts:
            continue
        for part in (path.stem, *path.parts):
            if pattern.fullmatch(part):
                keys.add(part)
    for path in sorted((ROOT / 'onto/phase_8_design/runs').glob('loop-*/round_*/*.json')):
        data = json.loads(path.read_text())
        if data.get('states') and data.get('inchikey'):
            keys.add(data['inchikey'])
    for path in sorted((ROOT / 'onto/phase_8_design/runs').glob('*/ledger.jsonl')):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            for row in json.loads(line).get('results', []):
                if any(row.get(field) is not None for field in ('E2_eV', 'dE_bind_kcal')):
                    key = row.get('inchikey') or _inchikey(row.get('smiles', ''))
                    if key:
                        keys.add(key)
    return keys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--binding', choices=['gp'], default='gp')
    p.add_argument('--library', type=Path, default=LIBRARY)
    p.add_argument('--out', type=Path, default=ROOT / 'dft/runs/funnel_gp')
    p.add_argument('--n', type=int, default=50)
    p.add_argument('--control-n', type=int, default=10)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--kappa', type=float, default=1.)
    args = p.parse_args()
    if args.n < 1 or args.control_n < 0:
        p.error('invalid candidate count')
    records = training_records()
    attached = [r for r in records if 'dE_bind_kcal' in r]
    e2_model, e2_loo, e2_scale = gp_e2(records)
    binding_model, binding_loo, binding_scale = gp_e2([{**r, 'E2_eV': r['dE_bind_kcal']} for r in attached])
    computed = computed_keys(records)
    with args.library.open(newline='') as f:
        library = list(csv.DictReader(f))
    candidates = []
    skipped = Counter()
    for row in library:
        reason = unsupported(row['smiles'])
        if reason:
            skipped[reason] += 1
            continue
        key = _inchikey(row['smiles'])
        if not key or (row.get('inchikey') and row['inchikey'] != key):
            skipped['inchikey_mismatch'] += 1
        elif key in computed:
            skipped['already_computed'] += 1
        else:
            candidates.append({**row, 'inchikey': key})
    if not candidates:
        raise ValueError('No uncomputed library candidates')
    smiles = [r['smiles'] for r in candidates]
    e2, e2std = e2_model.predict(smiles)
    binding, bindingstd = binding_model.predict(smiles)
    e2std *= e2_scale
    bindingstd *= binding_scale
    common = json.loads(COMMON.read_text())['states']
    if not all(_done(common.get(k)) for k in ('O2', 'O2_radical_anion')):
        raise ValueError('O2 reference states are incomplete')
    oxygen = (common['O2_radical_anion']['energy'] - common['O2']['energy']) * 27.2114
    calib = load_calibration(CALIB) if CALIB.exists() else None
    line = json.loads((ROOT / 'dft/runs/ref_set/lines.json').read_text())['v2']
    scored = []
    for row, e, es, b, bs in zip(candidates, e2, e2std, binding, bindingstd):
        raw = oxygen - float(e)
        margin = raw + (float(calib[classify(row['smiles'])]['mean_shift']) if calib else 0.)
        f = (line['a'] * float(e) + line['b'] - float(b)) / line['sigma']
        fs = math.hypot(line['a'] * float(es), float(bs)) / line['sigma']
        scored.append({**row, 'id': row.get('id') or row['inchikey'], 'E2_pred': float(e), 'E2_std': float(es),
                       'e2_std': float(es), 'dEbind_pred': float(b), 'dEbind_std': float(bs), 'f_pred': f,
                       'f_std': fs, 'raw_margin': raw, 'margin_pred': margin,
                       'o2_calibration': 'calibrated' if calib else 'uncalibrated'})
    selected, _ = pick_candidates(scored, args.n, 0, args.seed, args.kappa)
    selected_keys = {row['inchikey'] for row in selected}
    _, control = pick_candidates([row for row in scored if row['inchikey'] not in selected_keys], 0, args.control_n, args.seed, args.kappa)
    fields = ['id', 'smiles', 'inchikey', 'core', 'E2_pred', 'E2_std', 'dEbind_pred', 'dEbind_std',
              'f_pred', 'f_std', 'raw_margin', 'margin_pred', 'o2_calibration', 'arm']
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    with CANDIDATES.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows([{**r, 'arm': 'gp'} for r in selected] + [{**r, 'arm': 'random'} for r in control])
    summary = {'library': len(library), 'skipped': dict(sorted(skipped.items())), 'eligible': len(candidates),
               'o2_plausible': sum(oxygen_plausible(r['margin_pred'], r['e2_std']) for r in scored),
               'selected': len(selected), 'random_control': len(control),
               'top_per_core': dict(sorted(Counter(r['core'] for r in selected).items())),
               'e2_training_n': len(records), 'e2_loo_rmse_ev': e2_loo,
               'binding_training_n': len(attached), 'binding_loo_rmse_kcal': binding_loo,
               'e2_std_scale': e2_scale, 'binding_std_scale': binding_scale,
               'o2_calibration': 'calibrated' if calib else 'uncalibrated',
               'library_sha256': sha(args.library), 'seed': args.seed, 'kappa': args.kappa}
    atomic_json(args.out / 'summary.json', summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if calib is None:
        print('UNCALIBRATED: final selection must be re-run after O2 calibration.')


if __name__ == '__main__':
    main()
