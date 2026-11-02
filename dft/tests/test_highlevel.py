import json
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel as hl


def test_summary_bq():
    # Published pilot TZ energies and mRRHO corrections (Eh).
    energies = {'Q': (-381.4956182139721, .05516427847703653),
                'Q_radical_anion': (-381.63325468083406, .05326173040521098),
                'Q_dianion': (-381.72926959650016, .052367332182200244),
                'adduct': (-570.3962603488534, .06354420390880477),
                'CO2': (-188.62467963389096, -.009034825322771667)}
    fc = 4.417
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for state, (energy, correction) in energies.items():
            folder = root / ('CO2' if state == 'CO2' else 'BQ')
            folder.mkdir(exist_ok=True)
            for level, data in [('tz', {'energy_Eh': energy}), ('svp', {'thermo': {'G_corr_Eh': correction}})]:
                (folder / f'{state}_{level}.json').write_text(json.dumps({'status': 'ok', **data}))
        row = hl.composite(root, 'BQ', fc)
        assert abs(row['E1_V'] + .619) < .01
        assert abs(row['E2_V'] + 1.779) < .01
        assert abs(row['dG_bind_1M_kcal'] + 15.76) < .01


def test_coordinates_and_resume():
    good = {'converged': True, 'geom_converged': True, 'error': None, 'xyz': '1\n\nO 1 2 3\n'}
    low = {'states': {name: good for name in ('Q', 'Q_radical_anion', 'Q_dianion')},
           'adducts': {'0': {**good, 'energy': -1, 'o_index': 0}, '7': {**good, 'energy': -2, 'o_index': 7}}}
    xyz, site = hl.start_geometry(low, 'adduct')
    assert xyz == 'O 1 2 3' and site == 7
    assert hl.start_geometry(low, 'Q')[0] == 'O 1 2 3'
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'Q_tz.json'
        path.write_text(json.dumps({'status': 'ok'}))
        hl.run_job({'path': str(path)}, runner=lambda _: (_ for _ in ()).throw(AssertionError('rerun')))


def test_jobs_and_failure():
    tasks = hl.jobs('/tmp/highlevel-test-output')
    assert len(tasks) == 34
    assert all(a['nao_tz'] >= b['nao_tz'] for a, b in zip(tasks, tasks[1:]))
    assert all(t['spec']['task'] == ('opt' if t['path'].endswith('_tz.json') else 'opt+freq') for t in tasks)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'failure.json'
        job = {**tasks[0], 'path': str(path)}
        def fail(_):
            raise MemoryError('Hessian out of memory')
        hl.run_job(job, runner=fail)
        data = json.loads(path.read_text())
        assert data['status'] == 'error' and 'Hessian out of memory' in data['error']
        called = []
        hl.run_job(job, runner=lambda spec: called.append(spec) or {'status': 'ok'})
        assert len(called) == 1 and json.loads(path.read_text())['status'] == 'ok'


def test_summary_inputs():
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / 'cache.json'
        key = hl.inputs()[0]['id']
        cache.write_text(json.dumps({key: {'status': 'found', 'cid': 123}}))
        with patch.object(hl, 'PUBCHEM_CACHE', cache):
            result = hl.summarize(tmp)
        assert result['molecules'][0]['pubchem_cid'] == 123
        assert '123' in (Path(tmp) / 'summary.md').read_text()
        assert len(result['molecules']) == 4
        row = result['molecules'][0]
        assert abs(row['low_f'] - 1.3788717309511884) < 1e-8
        assert abs(row['low_O2_margin_V'] - .1756098125964427) < 1e-8
        assert result['molecules'][-1]['experiment']['E2_V'] == -1.18
        assert (Path(tmp) / 'summary.md').exists()


if __name__ == '__main__':
    test_summary_bq()
    test_coordinates_and_resume()
    test_jobs_and_failure()
    test_summary_inputs()
    print('highlevel tests passed')
