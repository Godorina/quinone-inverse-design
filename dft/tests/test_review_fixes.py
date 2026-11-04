"""Regression checks for DFT review fixes; no calculations are run."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import highlevel as hl
import run_set
from test_run_set import result, fake_record, adduct_xyz


class ReviewFixes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        states = {'CO2': result(-20), 'O2': result(-30), 'O2_radical_anion': result(-29.5)}
        (self.out / '_common.json').write_text(json.dumps({'states': states}))

    def record(self, index, smiles=None, explicit_class=None):
        record = fake_record(index)
        if smiles:
            record['smiles'] = smiles
        if explicit_class:
            record['class'] = explicit_class
        (self.out / f'KEY{index:02d}.json').write_text(json.dumps(record))
        return record

    def test_summary_does_not_inherit_previous_fit(self):
        for i in range(10):
            self.record(i)
        (self.out / 'summary.json').write_text(json.dumps({'line': {'n': 12}}))
        summary = run_set.summarize(self.out)
        self.assertEqual(summary['line']['n'], 10)
        self.assertNotIn('line_v1', summary)

    def test_original_families_and_explicit_class(self):
        smiles = ['O=C1C=CC(=O)C=C1', 'O=C1C=CC(=O)c2ccccc21',
                  'O=C1c2ccccc2C(=O)c2ccccc21', 'O=C1C(=O)c2ccccc2-c2ccccc21']
        for i, smi in enumerate(smiles):
            self.record(i, smi)
        self.record(4, smiles[0], 'custom')
        self.assertEqual([row['family'] for row in run_set.summarize(self.out)['molecules']],
                         ['BQ', 'NQ', 'AQ', 'PQ', 'custom'])

    def test_attached_adduct_selected_and_detached_fallback(self):
        rec = self.record(0)
        rec['adducts']['1'] = {**result(-99, adduct_xyz(2.5)), 'o_index': 0}
        (self.out / 'KEY00.json').write_text(json.dumps(rec))
        row = run_set.summarize(self.out)['molecules'][0]
        self.assertAlmostEqual(row['co2_distance'], 1.45)
        self.assertFalse(row['co2_detached'])
        self.assertEqual(hl.start_geometry(rec, 'adduct')[0], '\n'.join(adduct_xyz(1.45).splitlines()[2:]).strip())
        rec['adducts']['2'] = {**result(-20, adduct_xyz(2.0)), 'o_index': 0}
        (self.out / 'KEY00.json').write_text(json.dumps(rec))
        self.assertEqual(run_set.summarize(self.out)['molecules'][0]['co2_distance'], 2.0)
        with patch.object(hl, 'inputs', return_value=[{'id': 'KEY00', 'smiles': rec['smiles'], 'source': 'test', 'low': rec}]):
            high = hl.summarize(self.out)['molecules'][0]
        self.assertAlmostEqual(high['low_dE_bind_kcal'], (-20 - (-10) - hl.read(hl.REF / '_common.json')['states']['CO2']['energy']) * 627.5)
        del rec['adducts']['2']
        del rec['adducts']['0']
        (self.out / 'KEY00.json').write_text(json.dumps(rec))
        self.assertTrue(run_set.summarize(self.out)['molecules'][0]['co2_detached'])

    def test_fixed_lines_and_strict_version(self):
        lines = json.loads((hl.REF / 'lines.json').read_text())
        self.assertEqual(lines['v1'], {'a': -8.971458339658367, 'b': -42.406668947099355,
                                       'sigma': 3.4349261629533934, 'n': 12})
        self.assertEqual(lines['v2'], {'a': -10.79814529768974, 'b': -47.556304329783046,
                                       'sigma': 3.237774743441207, 'n': 18})
        self.assertEqual(hl.SETS['v1'][2], 'v1')
        self.assertEqual(hl.SETS['v2'][2], 'v2')
        with self.assertRaises(KeyError):
            hl.summarize(self.out, hl.SETS['v1'][0], 'missing')

    def test_explicit_sources_reproduce_recorded_low_f(self):
        for version in ('v1', 'v2'):
            smiles, folder, line = hl.SETS[version]
            saved = json.loads((folder / 'summary.json').read_text())
            with patch.object(Path, 'glob', side_effect=AssertionError('source glob used')):
                rows = hl.summarize(self.out, smiles, line)['molecules']
            self.assertEqual([r['low_source'] for r in rows], [r['low_source'] for r in saved['molecules']])
            for row, previous in zip(rows, saved['molecules']):
                self.assertAlmostEqual(row['low_f'], previous['low_f'], places=12)


if __name__ == '__main__':
    unittest.main()
