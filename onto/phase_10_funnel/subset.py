"""Deterministic size-limited, stratified Morgan/Tanimoto MaxMin subset."""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from rdkit import Chem
from rdkit.SimDivFilters.rdSimDivPickers import MaxMinPicker
from surrogate import fp
from enumerate import ROOT


def quotas(counts, size, minimum=10):
    if size < 0 or minimum < 0: raise ValueError('size and minimum must be nonnegative')
    if size > sum(counts.values()): raise ValueError('subset exceeds eligible population')
    base = {k: min(minimum, n) for k, n in counts.items()}
    if sum(base.values()) > size: raise ValueError('subset too small for minimum per core')
    remaining = set(counts)
    result = {}
    while remaining:
        available = size - sum(result.values())
        total = sum(math.sqrt(counts[k]) for k in remaining)
        if not total: return {**result, **{k: 0 for k in remaining}}
        desired = {k: available * math.sqrt(counts[k]) / total for k in remaining}
        constrained = [k for k in sorted(remaining) if desired[k] < base[k] or desired[k] > counts[k]]
        if constrained:
            # Fix one bound at a time and recompute, avoiding over-allocation.
            k = constrained[0]
            result[k] = base[k] if desired[k] < base[k] else counts[k]
            remaining.remove(k)
            continue
        result.update({k: math.floor(desired[k]) for k in remaining})
        extra = size - sum(result.values())
        for k in sorted(remaining, key=lambda k: (-(desired[k] % 1), k))[:extra]: result[k] += 1
        break
    return dict(sorted(result.items()))


def time_model():
    """Least-squares seconds = coefficient * heavy_atoms**2.5, no intercept."""
    points = []
    for path in sorted((ROOT / 'dft/runs/ref_set').glob('*.json')):
        try:
            data = json.loads(path.read_text()); states = data['states']
            pair = [states[k] for k in ('Q_radical_anion', 'Q_dianion')]
            if not all(x.get('converged') and x.get('geom_converged') and not x.get('error') for x in pair): continue
            mol = Chem.MolFromSmiles(data['smiles'])
            if mol is None: continue
            t = sum(float(x['seconds']) for x in pair)
            if not math.isfinite(t) or t <= 0: continue
            points.append((mol.GetNumHeavyAtoms() ** 2.5, t))
        except (KeyError, TypeError, ValueError): continue
    if not points:
        # Previous BQ benchmark: 127.6 seconds for 8 heavy atoms.
        return 127.6 / (8 ** 2.5), 0
    return sum(x*y for x, y in points) / sum(x*x for x, y in points), len(points)


def choose(rows, size=300, minimum=10, seed=0):
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        mol = Chem.MolFromSmiles(row['smiles'])
        if not mol: raise ValueError('Invalid SMILES in library')
        if row['inchikey'] in seen: raise ValueError('Duplicate InChIKey in library')
        seen.add(row['inchikey'])
        heavy = mol.GetNumHeavyAtoms()
        if heavy <= 20: groups[row['core']].append((row, heavy))
    counts = {k: len(v) for k, v in groups.items()}
    allocation = quotas(counts, size, minimum)
    coefficient, _ = time_model()
    selected = []
    for core, n in allocation.items():
        entries = sorted(groups[core], key=lambda pair: pair[0]['inchikey'])
        fingerprints = [fp(row['smiles']) for row, _ in entries]
        indices = MaxMinPicker().LazyBitVectorPick(fingerprints, len(entries), n, seed=seed) if n else []
        for i in indices:
            row, heavy = entries[i]
            selected.append({**row, 'heavy_atoms': heavy, 'estimated_gpu_seconds': round(coefficient * heavy ** 2.5, 2)})
    return selected


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--library', type=Path, default=Path(__file__).with_name('library.csv'))
    p.add_argument('--out', type=Path, default=Path(__file__).with_name('tier1_subset.csv'))
    p.add_argument('--size', type=int, default=300)
    p.add_argument('--minimum', type=int, default=10)
    p.add_argument('--seed', type=int, default=0)
    args = p.parse_args()
    with args.library.open() as handle: rows = list(csv.DictReader(handle))
    selected = choose(rows, args.size, args.minimum, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', newline='') as handle:
        fields = list(rows[0]) + ['heavy_atoms', 'estimated_gpu_seconds']
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(selected)
    coefficient, n = time_model()
    print(json.dumps({'eligible': sum(Chem.MolFromSmiles(r['smiles']).GetNumHeavyAtoms() <= 20 for r in rows), 'subset': len(selected),
                      'per_core': dict(sorted(Counter(r['core'] for r in selected).items())), 'seed': args.seed,
                      'time_fit_reference_count': n, 'time_coefficient': coefficient,
                      'estimated_serial_gpu_hours': round(sum(r['estimated_gpu_seconds'] for r in selected) / 3600, 2)}, indent=2))

if __name__ == '__main__': main()
