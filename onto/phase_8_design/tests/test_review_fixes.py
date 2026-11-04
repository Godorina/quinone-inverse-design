import json
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_8_design'))
import closed_loop
import generate
import loop


class ReviewFixes(unittest.TestCase):
    def test_quinone_ring_and_references(self):
        for value in ('O=C1CC(=O)c2ccccc21', 'O=C1CCC(=O)CC1',
                      'O=C1CNC(=O)CN1', 'O=C1CCC(=O)N1',
                      'O=C1C=CC(=O)N1', 'O=C1C(=O)Nc2ccccc21'):
            with self.subTest(value=value):
                self.assertEqual(loop.t0(value), 'not_quinone')
        summary = json.loads((ROOT / 'dft/runs/ref_set/summary.json').read_text())
        self.assertEqual(len(summary['molecules']), 21)
        for row in summary['molecules']:
            data = json.loads((ROOT / 'dft/runs/ref_set' / (row['inchikey'] + '.json')).read_text())
            with self.subTest(smiles=data['smiles']):
                self.assertIsNone(loop.t0(data['smiles']))
        for smiles in loop.QUINONES:
            with self.subTest(smiles=smiles):
                self.assertIsNone(loop.t0(smiles))
        highlevel = json.loads((ROOT / 'dft/runs/highlevel_v2/summary.json').read_text())
        for row in highlevel['molecules'][:2]:
            with self.subTest(smiles=row['smiles']):
                self.assertIsNone(loop.t0(row['smiles']))

    def test_radical_isotope_and_total_charge(self):
        self.assertIsNotNone(loop.t0('O=C1C([O])=CC(=O)C=C1'))
        self.assertIsNotNone(loop.t0('O=[13C]1C=CC(=O)C=C1'))
        self.assertIsNone(loop.t0('O=C1C([N+](=O)[O-])=CC(=O)C=C1'))
        self.assertIsNotNone(loop.t0('O=C1C=CC(=O)C=C1.[Na+]'))

    def test_oxygen_margin(self):
        self.assertIsNone(loop.objective(.4, -1, 2, 0, 2, .1))
        self.assertIsNotNone(loop.objective(.1, -1, 2, 0, 2, .4))
        self.assertIsNotNone(loop.objective(.25, -1, 2, 0, 2, .5, margin=.25))
        self.assertEqual(loop._score(lambda _: dict(E2=.4, dG=-1, a=2, b=0, sigma=2, o2_E=.1), 'x')[1]['reason'], 'o2_fail')

    def test_nonlegacy_substituents(self):
        f = 'O=C1C(F)=CC(=O)c2nccnc21'
        cl = 'O=C1C(Cl)=CC(=O)c2nccnc21'
        self.assertNotEqual(generate._substituents(f), generate._substituents(cl))
        self.assertEqual(generate._substituents(f), generate._substituents(f))

    def test_config_resume_and_line_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = ['--rounds', '1', '--per-round', '2', '--arm', 'llm', '--domain', 'v1', '--seed', '3']
            closed_loop.main(args + ['--out', tmp], llm=lambda _: {'proposals': []})
            out = Path(tmp)
            config = json.loads((out / 'config.json').read_text())
            self.assertEqual((config['domain'], config['seed'], config['per_round']), ('v1', 3, 2))
            record = json.loads((out / 'round_1/completed.json').read_text())
            self.assertEqual(record['line'], generate.context()['line'])
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    closed_loop.main(['--resume', tmp, '--domain', 'v2', '--seed', '3', '--per-round', '2', '--dry-run'])
            for option in (['--arm', 'random'], ['--domain', 'v2'], ['--seed', '4'],
                           ['--per-round', '3'], ['--reject-pubchem'], ['--extra-ref', tmp]):
                with self.subTest(option=option), self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                    closed_loop.main(args + ['--resume', tmp, '--dry-run'] + option)
        with tempfile.TemporaryDirectory() as tmp:
            closed_loop.main(['--resume', tmp, '--dry-run'])
            self.assertFalse((Path(tmp) / 'config.json').exists())

    def test_compare_different_lines(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for path, slope in ((a, 1), (b, 2)):
                record = {'round': 1, 'arm': 'llm', 'results': [], 'line': {'a': slope, 'b': 0, 'sigma': 1, 'n': 12}}
                (Path(path) / 'ledger.jsonl').write_text(json.dumps(record) + '\n')
            with self.assertRaisesRegex(ValueError, 'line'):
                closed_loop.compare_runs(a, b)
            (Path(b) / 'ledger.jsonl').write_text(json.dumps({'round': 1, 'results': []}) + '\n')
            self.assertIn('WARNING', closed_loop.compare_runs(a, b))


if __name__ == '__main__':
    unittest.main()
