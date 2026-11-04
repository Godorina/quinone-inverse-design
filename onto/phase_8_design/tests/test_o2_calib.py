import hashlib
import json
import sys
from pathlib import Path

import math
import tempfile
from contextlib import contextmanager

@contextmanager
def raises(error):
    try:
        yield
    except error:
        return
    raise AssertionError(f"Expected {error}")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from closed_loop import main, score, o2_feasible

CALIB = {'carbocyclic': {'mean_shift': -.2, 'sd': .1, 'n': 3}, 'heterocyclic': {'mean_shift': -.4, 'sd': .1, 'n': 2}}
LINE = {'a': 1, 'b': 0, 'sigma': 2}
ROW = {'smiles': 'O=C1C=CC(=O)C=C1', 'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -6, 'co2_detached': False}


def test_score_and_parent_gate():
    original = score(ROW, LINE)
    assert math.isclose(original['margin'], .3) and original['success']
    result = score(ROW, LINE, CALIB)
    assert math.isclose(result['raw_margin'], .3)
    assert math.isclose(result['margin'], .1)
    assert not result['success'] and not o2_feasible([result])
    assert score(ROW, LINE) == original


def test_config_and_resume(tmp_path):
    calibration = tmp_path / 'calib.json'
    calibration.write_text(json.dumps(CALIB))
    out = tmp_path / 'run'
    main(['--dry-run', '--out', str(out), '--o2-calib', str(calibration)])
    config = json.loads((out / 'config.json').read_text())
    assert config['o2_calib']['path'] == str(calibration.resolve())
    assert config['o2_calib']['sha256'] == hashlib.sha256(calibration.read_bytes()).hexdigest()
    prompt = (out / 'round_1/prompt_1.txt').read_text()
    assert 'calibrated' in prompt.lower()
    calibration.write_text(json.dumps({**CALIB, 'carbocyclic': {**CALIB['carbocyclic'], 'mean_shift': -.3}}))
    with raises(SystemExit):
        main(['--dry-run', '--resume', str(out), '--o2-calib', str(calibration)])


def test_calibrated_round(tmp_path):
    import csv
    from rdkit import Chem
    calibration = tmp_path / 'calib.json'
    calibration.write_text(json.dumps(CALIB))
    out = tmp_path / 'run'
    smiles = 'O=C1C=C(Cl)C(=O)C=C1'
    def llm(text):
        assert 'calibrated' in text.lower()
        return {'structured_output': {'proposals': [{'parent_id': 'D01', 'smiles': smiles, 'cited_ids': ['K001']}]}}
    def evaluator(path):
        rows = list(csv.DictReader((path / 'input.csv').open()))
        return {'molecules': [{'inchikey': Chem.MolToInchiKey(Chem.MolFromSmiles(r['smiles'])), 'E2_eV': -2, 'E_O2_eV': -1.7, 'dE_bind_kcal': -30, 'co2_detached': False} for r in rows]}
    main(['--rounds', '1', '--per-round', '1', '--out', str(out), '--o2-calib', str(calibration)], llm=llm, evaluator=evaluator, lookup=lambda _: {'cid': None, 'status': 'not_found'})
    record = json.loads((out / 'ledger.jsonl').read_text())
    assert len(record['results']) == 1
    result = record['results'][0]
    assert math.isclose(result['raw_margin'], .3) and math.isclose(result['calibrated_margin'], .1)
    assert not result['success'] and record['o2_calib']['sha256']


if __name__ == '__main__':
    test_score_and_parent_gate()
    with tempfile.TemporaryDirectory() as tmp:
        test_config_and_resume(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_calibrated_round(Path(tmp))
    print('3 passed')
