"""Reject unclassifiable calibrated proposals before lookup or evaluation."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import closed_loop

BAD = 'O=C1C=C(Cl)C(=O)C=C1'
CALIB = {'carbocyclic': {'mean_shift': -.2, 'sd': .1, 'n': 3}, 'heterocyclic': {'mean_shift': -.4, 'sd': .1, 'n': 3}}


def test_reject():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calib = root / 'calib.json'
        calib.write_text(json.dumps(CALIB))
        old = closed_loop.classify
        def classify(smiles):
            if smiles == BAD:
                raise ValueError('not classifiable')
            return old(smiles)
        def llm(_):
            return {'structured_output': {'proposals': [{'smiles': BAD, 'parent_id': 'D01', 'cited_ids': ['K001']}]}}
        with patch.object(closed_loop, 'check', return_value=None), patch.object(closed_loop, 'classify', side_effect=classify):
            out = closed_loop.main(['--rounds', '1', '--per-round', '1', '--out', str(root / 'run'), '--o2-calib', str(calib)], llm=llm,
                evaluator=lambda _: (_ for _ in ()).throw(AssertionError('evaluation called')),
                lookup=lambda _: (_ for _ in ()).throw(AssertionError('lookup called')))
        record = json.loads((out / 'ledger.jsonl').read_text())
        assert not record['accepted'] and record['rejected']
        assert all(x['reason'] == 'unclassifiable' for x in record['rejected'])


def test_random_arm_and_unmodified_uncalibrated():
    import csv
    from rdkit import Chem
    good = 'NC1=C(Br)C(=O)C(Br)=C(Br)C1=O'
    def evaluator(path):
        rows = list(csv.DictReader((path / 'input.csv').open()))
        return {'molecules': [{'inchikey': Chem.MolToInchiKey(Chem.MolFromSmiles(row['smiles'])), 'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -30, 'co2_detached': False} for row in rows]}
    def lookup(_):
        return {'cid': None, 'status': 'not_found'}
    old = closed_loop.classify
    def classify(smiles):
        if smiles == BAD:
            raise ValueError('not classifiable')
        return old(smiles)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calib = root / 'calib.json'
        calib.write_text(json.dumps(CALIB))
        with patch.object(closed_loop, 'check', return_value=None), patch.object(closed_loop, 'edit', side_effect=[BAD, good]), patch.object(closed_loop, 'classify', side_effect=classify):
            out = closed_loop.main(['--rounds', '1', '--per-round', '1', '--arm', 'random', '--out', str(root / 'random'), '--o2-calib', str(calib)], evaluator=evaluator, lookup=lookup)
        record = json.loads((out / 'ledger.jsonl').read_text())
        assert record['rejected'][0]['reason'] == 'unclassifiable'
        assert record['accepted'][0]['smiles'] == good
        def llm(_):
            return {'structured_output': {'proposals': [{'smiles': BAD, 'parent_id': 'D01', 'cited_ids': ['K001']}]}}
        with patch.object(closed_loop, 'check', return_value=None), patch.object(closed_loop, 'classify', side_effect=AssertionError('classify without calibration')):
            out = closed_loop.main(['--rounds', '1', '--per-round', '1', '--out', str(root / 'raw')], llm=llm, evaluator=evaluator, lookup=lookup)
        assert json.loads((out / 'ledger.jsonl').read_text())['accepted'][0]['smiles'] == BAD


if __name__ == '__main__':
    test_reject()
    test_random_arm_and_unmodified_uncalibrated()
    print('2 passed')
