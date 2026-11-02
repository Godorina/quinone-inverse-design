import csv
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import closed_loop as c
from generate import context, check, _inchikey


def evaluate(path):
    with (path / 'input.csv').open() as f:
        return {'molecules': [{'inchikey': _inchikey(r['smiles']), 'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -30, 'co2_detached': False} for r in csv.DictReader(f)]}


def test_extra():
    ctx = context()
    line, dft = dict(ctx['line']), list(ctx['dft'])
    smiles = 'O=C1C(F)=C(Cl)C(=O)C(Cl)=C1'
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / 'round_1'; p.mkdir()
        state = {'converged': True, 'geom_converged': True}
        (p / 'm.json').write_text(json.dumps({'smiles': smiles, 'states': {k: state for k in ('Q', 'Q_radical_anion', 'Q_dianion')}, 'adducts': {'0': state}}))
        (p / 'bad.json').write_text(json.dumps({'smiles': 'bad', 'states': {}}))
        c.add_extra_refs(ctx, [Path(tmp)])
        assert smiles in ctx['ref_fps'] and ctx['line'] == line and ctx['dft'] == dft
        assert check({'smiles': smiles, 'parent_id': 'D01', 'cited_ids': []}, ctx, ctx['extra_seen']) == 'duplicate'


def test_refill_and_resume():
    smiles = ['O=C1C=C(Cl)C(=O)C=C1', 'NC1=C(Br)C(=O)C(Br)=C(Br)C1=O', 'NC1=C(Cl)C(=O)C(Cl)=C(Cl)C1=O']
    proposal = lambda s: {'parent_id': 'D01', 'smiles': s, 'cited_ids': []}
    with tempfile.TemporaryDirectory() as tmp:
        calls = []
        def llm(text):
            calls.append(text)
            return {'proposals': ([proposal(smiles[0]), {'smiles': 'c1ccccc1'}] if len(calls) == 1 else [proposal(smiles[len(calls)-1])]), 'total_cost_usd': .1}
        c.main(['--rounds', '1', '--per-round', '3', '--out', tmp], llm=llm, evaluator=evaluate)
        assert len(calls) == 3 and 'not_quinone' in calls[1] and smiles[0] in calls[1]
        record = json.loads((Path(tmp) / 'round_1/completed.json').read_text())
        assert len(record['accepted']) == 3 and len(record['rejected']) == 1 and abs(record['cost'] - .3) < 1e-8
        (Path(tmp) / 'round_1/completed.json').unlink()
        c.main(['--rounds', '1', '--per-round', '3', '--resume', tmp], llm=lambda _: 1/0, evaluator=evaluate)
        assert len(json.loads((Path(tmp) / 'round_1/completed.json').read_text())['accepted']) == 3
    with tempfile.TemporaryDirectory() as tmp:
        calls = []
        c.main(['--rounds', '1', '--per-round', '3', '--out', tmp], llm=lambda _: (calls.append(1) or {'proposals': []}), evaluator=lambda _: 1/0)
        assert len(calls) == 3 and json.loads((Path(tmp) / 'round_1/completed.json').read_text())['accepted'] == []


def test_random_and_compare():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        for out in (a, b):
            c.main(['--rounds', '2', '--per-round', '3', '--arm', 'random', '--seed', '7', '--out', out], llm=lambda _: 1/0, evaluator=evaluate)
        def records(out):
            return [json.loads(x) for x in (Path(out) / 'ledger.jsonl').read_text().splitlines()]
        x, y = records(a), records(b)
        assert [[p['smiles'] for p in r['accepted']] for r in x] == [[p['smiles'] for p in r['accepted']] for r in y]
        assert all(len(r['accepted']) == 3 for r in x)
        ctx = context(); seen = set()
        for r in x:
            for p in r['accepted']:
                assert check(p, ctx, seen) is None
                seen.add(_inchikey(p['smiles']))
        table = c.compare_runs(a, b)
        assert '| 1 |' in table and '| 2 |' in table and 'random' in table
        assert 'random' in (Path(a) / 'report.md').read_text()


if __name__ == '__main__':
    test_extra(); test_refill_and_resume(); test_random_and_compare()
    print('3 passed')
