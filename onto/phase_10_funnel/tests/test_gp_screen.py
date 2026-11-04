"""CPU-only GP screening and calibration regression tests."""
import csv
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_10_funnel'))
import mlp_screen


class GPScreenTest(unittest.TestCase):
    def test_gp_screen(self):
        gp = importlib.import_module('gp_screen')
        samples = ['O=C1C=CC(=O)C=C1', 'O=C1C(F)=CC(=O)C=C1',
                   'O=C1C(Cl)=CC(=O)C=C1', 'O=C1C(Br)=CC(=O)C=C1',
                   'O=C1C(C)=CC(=O)C=C1', 'O=C1C(C#N)=CC(=O)C=C1']
        records = [{'smiles': s, 'inchikey': mlp_screen._inchikey(s),
                    'E2_eV': -3.0 - i*.1, 'dE_bind_kcal': -10-i} for i, s in enumerate(samples[:3])]
        self.assertIsNone(gp.unsupported(samples[3]))
        self.assertTrue(gp.unsupported('O=C1C([I])=CC(=O)C=C1'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            lib = path / 'library.csv'
            with lib.open('w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=['smiles', 'inchikey', 'core']); w.writeheader()
                for s in samples:
                    w.writerow({'smiles': s, 'inchikey': mlp_screen._inchikey(s), 'core': 'BQ'})
            output = path / 'candidates.csv'
            with patch.object(gp, 'training_records', return_value=records), patch.object(gp, 'computed_keys', return_value={r['inchikey'] for r in records}), \
                 patch.object(gp, 'CALIB', path / 'missing'), patch.object(gp, 'CANDIDATES', output), \
                 patch.object(sys, 'argv', ['gp_screen', '--library', str(lib), '--out', str(path), '--n', '2', '--control-n', '1']):
                gp.main()
            with output.open() as f:
                rows = list(csv.DictReader(f))
            self.assertTrue(rows)
            self.assertTrue(any(r['inchikey'] == mlp_screen._inchikey(samples[3]) for r in rows))
            self.assertFalse({r['inchikey'] for r in rows} & {r['inchikey'] for r in records})
            self.assertEqual({r['arm'] for r in rows}, {'gp', 'random'})
            self.assertEqual(len(rows), len({r['inchikey'] for r in rows}))
            self.assertTrue(all(r['o2_calibration'] == 'uncalibrated' for r in rows))
            self.assertTrue(all(float(r['dEbind_std']) >= 0 and float(r['f_std']) >= 0 for r in rows))

    def test_calibration_gate(self):
        rows = [{'mlp_ev': x, 'dft_kcal': y} for x, y in [(0, 0), (1, 1), (2, -1), (3, 1), (4, -1)]]
        result = mlp_screen.fit_calibration(rows)
        self.assertIn('baseline_loo_rmse', result)
        self.assertTrue(mlp_screen.calibration_warning(result))
        good = mlp_screen.fit_calibration([{'mlp_ev': x, 'dft_kcal': 2*x+3} for x in range(5)])
        self.assertFalse(mlp_screen.calibration_warning(good))


if __name__ == '__main__':
    unittest.main()
