import json
import math
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'onto/phase_10_funnel'),str(ROOT/'onto/phase_8_design'),str(ROOT/'dft')]
import mlp_screen as screen
import mlp_worker as worker


class MLPScreenTests(unittest.TestCase):
    def test_fit_and_loo(self):
        data=[{'mlp_ev':x,'dft_kcal':2*x+3,'class':'carbocyclic','training_core':'unknown'} for x in (1.,2.,3.,4.)]
        fit=screen.fit_calibration(data)
        self.assertAlmostEqual(fit['alpha'],2.)
        self.assertAlmostEqual(fit['beta'],3.)
        self.assertAlmostEqual(fit['loo_rmse'],0.)
        self.assertEqual(fit['n'],4)
        with self.assertRaises(ValueError): screen.fit_calibration(data[:2])

    def test_rank_optimistic_gate_and_diversity(self):
        self.assertTrue(screen.oxygen_plausible(.10,.06))
        self.assertFalse(screen.oxygen_plausible(.08,.06))
        rows=[{'smiles':'O=C1C=CC(=O)C=C1','inchikey':'A','margin_pred':.1,'e2_std':.1,'f_pred':2.,'f_std':.2},
              {'smiles':'O=C1C(F)=CC(=O)C=C1','inchikey':'B','margin_pred':.0,'e2_std':.01,'f_pred':5.,'f_std':.1}]
        selected,control=screen.pick_candidates(rows, n=2, control_n=1, seed=0)
        self.assertEqual([x['inchikey'] for x in selected],['A'])
        self.assertEqual([x['inchikey'] for x in control],['A'])

    def test_worker_attachment_and_resume(self):
        self.assertEqual(worker.best_attached({'0':{'converged':True,'detached':False,'energy_ev':-3},'1':{'converged':True,'detached':True,'energy_ev':-7}})['energy_ev'],-3)
        self.assertIsNone(worker.best_attached({'0':{'converged':True,'detached':True,'energy_ev':-7}}))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'one.json'; calls=[]
            job={'inchikey':'X','smiles':'C','symbols':['C','O'], 'coords':[[0,0,0],[1,0,0]], 'sites':[1]}
            def fake(symbols,coords,calc,fmax,maxsteps):
                calls.append(len(symbols)); return {'symbols':symbols,'coords':np.array(coords).tolist(),'energy_ev':-len(symbols),'converged':True,'steps':1,'seconds':.01,'fmax':0.}
            with patch.object(worker,'relax',side_effect=fake):
                first=worker.run_one(job,p,None,0.,'cfg',.05,300)
                second=worker.run_one(job,p,None,0.,'cfg',.05,300)
            self.assertEqual(calls,[2,5]); self.assertEqual(first,second)
            self.assertAlmostEqual(first['delta_e_mlp_ev'],-3.)
            with self.assertRaises(ValueError): worker.run_one(job,p,None,0.,'other',.05,300)

    def test_no_br(self):
        self.assertEqual(screen.unsupported('O=C1C(Br)=CC(=O)C=C1'), 'unsupported_element:Br')
        self.assertIsNone(screen.unsupported('O=C1C(F)=CC(=O)C=C1'))
        self.assertEqual(screen.unsupported('C[NH3+]'), 'outside_domain:charged_or_disconnected')

    def test_candidate_csv_uses_unrecalibrated_o2_and_runs_direct(self):
        import csv
        import hashlib
        import tier2
        samples = ['O=C1C=CC(=O)C=C1', 'O=C1C(F)=CC(=O)C=C1',
                   'O=C1C(Cl)=CC(=O)C=C1', 'O=C1C(C)=CC(=O)C=C1']
        records = [{'smiles': s, 'inchikey': screen._inchikey(s), 'E2_eV': -3.0 + i * .02} for i, s in enumerate(samples)]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); model = td / 'model'; model.write_bytes(b'toy')
            out = td / 'mlp'; out.mkdir(); library = td / 'library.csv'; output = td / 'dft_candidates.csv'
            with library.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['smiles', 'inchikey', 'core', 'substituents', 'sa_score'], extrasaction='ignore')
                writer.writeheader()
                for r in records: writer.writerow({**r, 'core': 'BQ', 'substituents': 'H', 'sa_score': 2.})
            model_sha = screen.sha(model)
            config = hashlib.sha256(json.dumps({'model':model_sha, 'fmax':.05, 'maxsteps':300, 'version':1}, sort_keys=True).encode()).hexdigest()
            (out / 'calibration.json').write_text(json.dumps({'model_sha256':model_sha, 'config':config, 'alpha':20., 'beta':0., 'loo_rmse':2.}))
            for r in records:
                (out / (r['inchikey'] + '.json')).write_text(json.dumps({'config':config, 'complete':True, 'detached':False, 'delta_e_mlp_ev':-1.}))
            argv = ['mlp_screen', '--candidates', '--model', str(model), '--out', str(out), '--library', str(library), '--n', '2']
            with patch.object(sys, 'argv', argv), patch.object(screen, 'training_records', return_value=records), \
                 patch.object(screen, 'CANDIDATES', output), patch.object(screen, 'CALIB', td / 'missing'):
                screen.main()
            with output.open() as f: selected = list(csv.DictReader(f))
            self.assertGreater(len(selected), 0)
            self.assertTrue(all(r['o2_calibration'] == 'uncalibrated' for r in selected))
            self.assertTrue((out / 'candidates_manifest.json').exists())
            seen = []
            def fake_execute(rows, *args): seen.extend(rows); return True
            args = SimpleNamespace(candidates=output, out=td/'tier2', calib=td/'missing')
            with patch.object(tier2, 'execute_round', side_effect=fake_execute):
                self.assertTrue(tier2.run_candidate_file(args, None, ['1']))
            self.assertEqual([r['inchikey'] for r in seen], [r['inchikey'] for r in selected])

    def test_co2_placement_matches_existing_dft_helper(self):
        from dft import co2_adduct
        symbols = ['C', 'O']; coords = np.array([[0., 0., 0.], [1.2, 0., 0.]])
        expected_symbols, expected = co2_adduct(symbols, coords, 1)
        actual_symbols, actual = worker.place_co2(symbols, coords, 1)
        self.assertEqual(actual_symbols, expected_symbols)
        np.testing.assert_allclose(actual, expected)

    @unittest.skipUnless(screen.BAM_PYTHON.exists() and screen.MODEL.exists(), 'BAM environment or checkpoint missing')
    def test_real_bq_cpu_smoke(self):
        smiles = 'O=C1C=CC(=O)C=C1'
        jobs, skipped = screen.build_jobs([{'smiles': smiles, 'inchikey': screen._inchikey(smiles)}])
        self.assertFalse(skipped)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            task = {'out': str(td), 'checkpoint': str(screen.MODEL), 'device': 'cpu',
                    'fmax': .05, 'maxsteps': 300, 'config': 'test-only', 'items': jobs}
            jobfile = td / 'job.json'; jobfile.write_text(json.dumps(task))
            env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                                                PYTHONPATH=str(screen.BAM_SOURCE), OMP_NUM_THREADS='1')
            subprocess.run([str(screen.BAM_PYTHON), str(ROOT/'onto/phase_10_funnel/mlp_worker.py'), str(jobfile)],
                           env=env, check=True, capture_output=True, text=True, timeout=180)
            result = json.loads((td / (jobs[0]['inchikey'] + '.json')).read_text())
            self.assertTrue(result['complete'])
            self.assertFalse(result['detached'])
            self.assertTrue(math.isfinite(result['delta_e_mlp_ev']))

    def test_device_selection_is_explicit_and_fails_closed(self):
        class FakeCUDA:
            def __init__(self): self.selected = None
            def is_available(self): return True
            def device_count(self): return 2
            def set_device(self, index): self.selected = index
            def current_device(self): return self.selected
        fake = SimpleNamespace(cuda=FakeCUDA())
        self.assertEqual(worker.configure_device('cuda:1', fake), 'cuda:1')
        self.assertEqual(fake.cuda.selected, 1)
        self.assertEqual(worker.configure_device('cpu', fake), 'cpu')
        with self.assertRaises(ValueError): worker.configure_device('cuda', fake)
        with self.assertRaises(RuntimeError): worker.configure_device('cuda:2', fake)

    def test_calibration_must_match_checkpoint(self):
        with self.assertRaises(ValueError): screen.validate_calibration({'model_sha256':'a'},'b')

if __name__ == '__main__': unittest.main()
