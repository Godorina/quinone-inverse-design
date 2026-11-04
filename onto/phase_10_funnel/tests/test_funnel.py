import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'onto/phase_10_funnel'))
sys.path.insert(0, str(ROOT / 'onto/phase_8_design'))
from loop import t0
import enumerate as enum
import tier1
import surrogate
import tier2


class FunnelTests(unittest.TestCase):
    def test_enumeration(self):
        a, stats = enum.enumerate_library(set(), limit=80)
        b, _ = enum.enumerate_library(set(), limit=80)
        self.assertEqual(a, b)
        self.assertEqual(len(a), len({x['inchikey'] for x in a}))
        self.assertTrue(all(t0(x['smiles']) is None and x['sa_score'] <= 4.5 for x in a))
        self.assertEqual(len(a), 80)

    def test_gate(self):
        row = tier1.gate('O=C1C=CC(=O)C=C1', -2.4, -2.3, {'carbocyclic': {'mean_shift': -0.04}}, .1)
        self.assertAlmostEqual(row['raw_margin'], .1)
        self.assertAlmostEqual(row['calibrated_margin'], .06)
        self.assertTrue(row['survives'])
        self.assertFalse(tier1.gate('O=C1C=CC(=O)C=C1', -2.4, -2.3, {'carbocyclic': {'mean_shift': -.06}}, .1)['survives'])

    def test_gp_and_diversity(self):
        train = ['O=C1C=CC(=O)C=C1', 'O=C1C(F)=CC(=O)C=C1', 'O=C1C(Cl)=CC(=O)C=C1']
        model = surrogate.GP(train, [0., 3., -2.])
        mean, std = model.predict(train)
        self.assertLess(sum((mean - [0., 3., -2.])**2), .1)
        choices = surrogate.select(train, [0., 3., -2.], [0., 0., 0.], 3, threshold=.7)
        self.assertEqual(choices[0], 1)
        self.assertTrue(all(surrogate.similarity(train[i], train[j]) < .7 for n, i in enumerate(choices) for j in choices[n+1:]))

    def test_gp_recovers_held_out_trend(self):
        import numpy as np
        smiles = ['O=C1C=CC(=O)C=C1', 'O=C1C(F)=CC(=O)C=C1',
                  'O=C1C(Cl)=CC(=O)C=C1', 'O=C1C(Br)=CC(=O)C=C1',
                  'O=C1C(C)=CC(=O)C=C1', 'O=C1C(O)=CC(=O)C=C1',
                  'O=C1C(N)=CC(=O)C=C1', 'O=C1C(C#N)=CC(=O)C=C1']
        target = np.array([3 * surrogate.similarity(s, smiles[1]) for s in smiles])
        model = surrogate.GP(smiles[:5], target[:5])
        predicted, _ = model.predict(smiles[5:])
        # An uninformed random constant predictor has expected MSE variance + squared bias.
        baseline = np.mean((target[5:, None] - target[None, :5]) ** 2)
        self.assertLess(np.mean((predicted - target[5:]) ** 2), baseline)

    def test_tier1_resume(self):
        calls = []
        def fake(symbols, coords, charge, spin, gpu):
            calls.append(charge)
            return {'converged': True, 'geom_converged': True, 'energy': float(charge), 'error': None}
        item = {'smiles': 'O=C1C=CC(=O)C=C1', 'inchikey': 'TEST'}
        with tempfile.TemporaryDirectory() as td:
            tier1.run_molecule(item, td, False, optimize_fn=fake)
            tier1.run_molecule(item, td, False, optimize_fn=fake)
            self.assertEqual(calls, [-1, -2])

    def test_tier2_fake_resume(self):
        selected = [{'inchikey': 'A', 'smiles': 'O=C1C=CC(=O)C=C1'}]
        calls = []
        def fake(items): calls.append(items)
        def summary(out):
            return {'molecules': [{'inchikey': 'A', 'E2_eV': -2., 'E_O2_eV': -1.8,
                                   'dE_bind_kcal': -20., 'co2_detached': False}]}
        line = {'a': -10., 'b': -40., 'sigma': 2.}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'ledger.jsonl'
            self.assertTrue(tier2.execute_round(selected, td, path, 1, line, None, fake, summary))
            self.assertTrue(tier2.execute_round(selected, td, path, 1, line, None, fake, summary))
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(tier2.read_ledger(path)), 1)

    def test_missing_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                tier1.load_calibration(Path(td) / 'missing.json')
            self.assertIsNone(tier1.load_calibration(Path(td) / 'missing.json', True))

    def test_ledger_resume(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'ledger.jsonl'
            tier2.append_ledger(p, {'round': 1, 'inchikey': 'A', 'f': 1})
            tier2.append_ledger(p, {'round': 1, 'inchikey': 'A', 'f': 1})
            self.assertEqual(len(tier2.read_ledger(p)), 1)
            with self.assertRaises(ValueError):
                tier2.append_ledger(p, {'round': 2, 'inchikey': 'A', 'f': 2})

if __name__ == '__main__':
    unittest.main()
