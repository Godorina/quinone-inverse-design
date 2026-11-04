"""Deterministically enumerate and filter substituted quinone scaffolds."""
import argparse
import csv
import itertools
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'onto/phase_8_design'))
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from generate import context, _inchikey, sa_score
from loop import _positions, t0

CORES = {
    '1,4-BQ': 'O=C1C=CC(=O)C=C1', '1,2-BQ': 'O=C1C(=O)C=CC=C1',
    '1,4-NQ': 'O=C1C=CC(=O)c2ccccc21', '1,2-NQ': 'O=C1C(=O)c2ccccc2C=C1',
    '9,10-AQ': 'O=C1c2ccccc2C(=O)c2ccccc21',
    '9,10-PQ': 'O=C1C(=O)c2ccccc2-c2ccccc21',
    'quinoxaline-5,8-dione': 'O=C1C=CC(=O)c2nccnc21',
    'quinoline-5,8-dione': 'O=C1C=CC(=O)c2ncccc21',
    'phenanthroline-5,6-dione': 'O=C1C(=O)c2cccnc2-c2ncccc21',
    'BDT-Q': 'O=C1c2ccsc2C(=O)c2ccsc21',
}
SUBS = {'F':'F', 'Cl':'Cl', 'Br':'Br', 'CN':'C#N', 'CF3':'C(F)(F)F', 'OMe':'OC', 'NH2':'N', 'OH':'O', 'Me':'C', 'SO2Me':'S(=O)(=O)C'}
SMALL = {'1,4-BQ', '1,2-BQ', '1,4-NQ', '1,2-NQ', 'quinoxaline-5,8-dione', 'quinoline-5,8-dione'}


def scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: raise ValueError(f'Invalid SMILES: {smiles}')
    return Chem.MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol))


CORE_SCAFFOLDS = {scaffold(value): name for name, value in CORES.items()}


@lru_cache(maxsize=None)
def _classify_scaffold(value):
    if value in CORE_SCAFFOLDS:
        return CORE_SCAFFOLDS[value]
    mol = Chem.MolFromSmiles(value)
    positions = [a.GetIdx() for a in mol.GetAtoms() if a.GetIsAromatic() and a.GetAtomicNum() == 7]
    # Prefer the closest named parent, so further aza-quinolines keep their parent.
    priority = {name: i for i, name in enumerate(reversed(CORES))}
    for count in range(1, len(positions) + 1):
        matches = []
        for indices in itertools.combinations(positions, count):
            editable = Chem.RWMol(mol)
            for idx in indices:
                editable.GetAtomWithIdx(idx).SetAtomicNum(6)
            try:
                Chem.SanitizeMol(editable)
                name = CORE_SCAFFOLDS.get(Chem.MolToSmiles(editable))
                if name: matches.append(name)
            except ValueError:
                continue
        if matches:
            return 'aza-' + min(matches, key=lambda name: priority[name])
    raise ValueError(f'Unrecognized quinone scaffold: {value}')


def classify_core(smiles):
    return _classify_scaffold(scaffold(smiles))


def has_nn(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return any(b.GetBeginAtom().GetAtomicNum() == 7 and b.GetEndAtom().GetAtomicNum() == 7 for b in mol.GetBonds())


def variants(smiles):
    mol = Chem.MolFromSmiles(smiles)
    yield mol
    positions = [a.GetIdx() for a in mol.GetAtoms() if a.GetIsAromatic() and a.GetAtomicNum() == 6 and a.GetTotalNumHs()]
    for n in (1, 2):
        for pair in itertools.combinations(positions, n):
            edit = Chem.RWMol(mol)
            for i in pair:
                edit.GetAtomWithIdx(i).SetAtomicNum(7)
            try:
                Chem.SanitizeMol(edit)
                yield Chem.Mol(edit)
            except ValueError:
                continue


def known_keys():
    ctx = context()
    keys = set(ctx['kg_inchikeys']) | {r['inchikey'] for r in ctx['dft']}
    keys |= {_inchikey(r['smiles']) for r in ctx['kg'] if r['smiles']}
    # Include all reference proposals and KG structures, not only measured KG rows.
    for path, field in ((ROOT / 'onto/phase_4b_extend/smiles_proposals.csv', 'canonical_smiles'),
                        (ROOT / 'onto/phase_4b_extend/reference_expansion.csv', 'smiles')):
        with path.open() as handle:
            keys.update(_inchikey(row[field]) for row in csv.DictReader(handle) if row.get(field))
    from rdflib import Graph
    from generate import KG, QN
    graph = Graph().parse(KG, format='turtle')
    keys.update(_inchikey(str(value)) for value in graph.objects(None, QN.smiles))
    keys.update(str(value) for value in graph.objects(None, QN.inchikey))
    keys.update(row['inchikey'] for row in json.loads((ROOT / 'dft/runs/ref_set/summary.json').read_text())['molecules'])
    for path in (ROOT / 'onto/phase_8_design/runs').glob('*/ledger.jsonl'):
        for line in path.read_text().splitlines():
            record = json.loads(line)
            for field in ('accepted', 'results', 'rejected'):
                for item in record.get(field, []):
                    if isinstance(item, dict) and item.get('smiles'):
                        keys.add(_inchikey(item['smiles']))
    return keys - {None, ''}


def enumerate_library(known, limit=100000):
    if limit < 1:
        raise ValueError('limit must be positive')
    rows, seen, stats = [], set(), Counter()
    for core, smiles in CORES.items():
        for mol in variants(smiles):
            positions = _positions(mol)
            for n in range(0, 3 if core in SMALL else 2):
                for pos in itertools.combinations(positions, n):
                    for names in itertools.product(SUBS, repeat=n):
                        candidate = Chem.Mol(mol)
                        if n:
                            editable = Chem.RWMol(mol)
                            for idx, name in zip(pos, names):
                                fragment = Chem.MolFromSmiles(SUBS[name])
                                offset = editable.GetNumAtoms()
                                editable.InsertMol(fragment)
                                editable.AddBond(idx, offset, Chem.BondType.SINGLE)
                            try:
                                Chem.SanitizeMol(editable)
                                candidate = editable.GetMol()
                            except ValueError:
                                candidate = None
                        stats['generated'] += 1
                        if candidate is None:
                            stats['invalid'] += 1
                            continue
                        value = Chem.MolToSmiles(candidate)
                        reason = t0(value)
                        if reason:
                            stats['t0_' + reason] += 1
                            continue
                        key = _inchikey(value)
                        if key in seen:
                            stats['duplicate'] += 1
                            continue
                        seen.add(key)
                        if key in known:
                            stats['known'] += 1
                            continue
                        sa = sa_score(value)
                        if sa is None or sa > 4.5:
                            stats['sa'] += 1
                            continue
                        if has_nn(value):
                            stats['nn'] += 1
                            continue
                        true_core = classify_core(value)
                        rows.append({'smiles': value, 'inchikey': key, 'core': true_core, 'substituents': ';'.join(names) or 'H', 'sa_score': round(sa, 4)})
                        stats['core:' + true_core] += 1
                        if len(rows) >= limit:
                            stats['capped'] = 1
                            return rows, stats
    return rows, stats


def timing_estimate():
    """Estimate serial GPU hours from recorded completed two-state timings."""
    seconds = []
    for path in (ROOT / 'dft/runs/ref_set').glob('*.json'):
        try:
            states = json.loads(path.read_text())['states']
            pair = [states[name] for name in ('Q_radical_anion', 'Q_dianion')]
            if all(x.get('converged') and x.get('geom_converged') and not x.get('error') for x in pair):
                seconds.append(sum(float(x['seconds']) for x in pair))
        except (KeyError, TypeError, ValueError):
            continue
    bench = json.loads((ROOT / 'dft/runs/bench_bq/result.json').read_text())['states']
    bq = sum(bench[name]['seconds'] for name in ('BQ_radical_anion', 'BQ_dianion'))
    return {'ref_count': len(seconds), 'ref_mean_seconds': round(statistics.mean(seconds), 1),
            'ref_median_seconds': round(statistics.median(seconds), 1),
            'hours_per_100_serial_gpu': round(statistics.mean(seconds) * 100 / 3600, 2),
            'bq_seconds': round(bq, 1)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100000)
    parser.add_argument('--out', type=Path, default=Path(__file__).with_name('library.csv'))
    args = parser.parse_args()
    RDLogger.DisableLog('rdApp.error')
    rows, stats = enumerate_library(known_keys(), args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['smiles', 'inchikey', 'core', 'substituents', 'sa_score'])
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'library': len(rows), 'per_core': {k[5:]: v for k, v in sorted(stats.items()) if k.startswith('core:')}, 'attrition': {k:v for k,v in stats.items() if not k.startswith('core:')}, 'timing_estimate': timing_estimate()}, indent=2))

if __name__ == '__main__':
    main()
