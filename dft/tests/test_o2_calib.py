import json
import sys
from pathlib import Path
from unittest.mock import patch

import math
import tempfile
import statistics
from contextlib import contextmanager

@contextmanager
def raises(error):
    try:
        yield
    except error:
        return
    raise AssertionError(f"Expected {error}")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel as h
from o2_calibration import classify


def test_classes():
    assert classify('O=C1C=CC(=O)c2nccnc21') == 'heterocyclic'
    assert classify('O=C1C=CC(=O)c2ccccc21') == 'carbocyclic'
    with raises(ValueError):
        classify('c1ccccc1')


def test_calibration_jobs_and_composite(tmp_path):
    candidates = h.SETS['calib'][0]
    assert len(candidates) == 9
    with patch('pyscf.gto.M') as molecule:
        molecule.return_value.nao = 1
        tasks = h.jobs(tmp_path, candidates, states=('Q_radical_anion', 'Q_dianion'))
    assert len(tasks) == 36
    assert all('adduct' not in x['path'] and 'CO2' not in x['path'] for x in tasks)
    key = h.inputs(candidates)[0]['id']
    folder = tmp_path / key
    folder.mkdir()
    for state, energy in [('Q_radical_anion', -100), ('Q_dianion', -100.1)]:
        for level in ('tz', 'svp'):
            (folder / f'{state}_{level}.json').write_text(json.dumps({'status': 'ok', 'opt_converged': True, 'energy_Eh': energy, 'thermo': {'G_corr_Eh': 0, 'n_imag': 0}}))
    row = h.composite(tmp_path, key, 4.0)
    assert 'E2_V' in row and 'O2_margin_V' in row and 'dG_bind_1M_kcal' not in row


def test_summary_requires_all_and_combines_unique_rows(tmp_path):
    candidates = h.SETS['calib'][0]
    calib = tmp_path / 'o2_calib.json'
    with raises(ValueError):
        h.summarize_calib(tmp_path, candidates, calib)
    assert not calib.exists()
    for item in h.inputs(candidates):
        folder = tmp_path / item['id']
        folder.mkdir()
        for state, energy in [('Q_radical_anion', -100), ('Q_dianion', -100.1)]:
            for level in ('tz', 'svp'):
                (folder / f'{state}_{level}.json').write_text(json.dumps({'status': 'ok', 'opt_converged': True, 'energy_Eh': energy, 'thermo': {'G_corr_Eh': 0, 'n_imag': 0}}))
    summary = h.summarize_calib(tmp_path, candidates, calib)
    assert len(summary['molecules']) == 15
    assert len({r['id'] for r in summary['molecules']}) == 15
    assert all({'low_E2_eV', 'low_O2_margin_V', 'E2_V', 'O2_margin_V', 'shift_V', 'class'} <= r.keys() for r in summary['molecules'])
    values = json.loads(calib.read_text())
    assert sum(v['n'] for v in values.values()) == 15
    for category, stats in values.items():
        shifts = [r['shift_V'] for r in summary['molecules'] if r['class'] == category]
        assert math.isclose(stats['mean_shift'], sum(shifts) / len(shifts))
        assert math.isclose(stats['sd'], statistics.stdev(shifts))


if __name__ == '__main__':
    test_classes()
    with tempfile.TemporaryDirectory() as tmp:
        test_calibration_jobs_and_composite(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_summary_requires_all_and_combines_unique_rows(Path(tmp))
    print('3 passed')
