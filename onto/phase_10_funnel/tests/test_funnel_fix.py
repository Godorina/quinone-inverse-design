import csv
import io
import json
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'onto/phase_10_funnel'), str(ROOT / 'onto/phase_8_design')]
import enumerate as enum
import subset
import tier1


class FunnelFixTests(unittest.TestCase):
    def test_actual_scaffold(self):
        for name, smiles in enum.CORES.items():
            self.assertEqual(enum.classify_core(smiles), name)
        self.assertEqual(enum.classify_core('O=C1C(F)=CC(=O)c2nccnc21'), 'quinoxaline-5,8-dione')
        self.assertEqual(enum.classify_core('O=C1C(F)=CC(=O)c2ncccc21'), 'quinoline-5,8-dione')
        self.assertEqual(enum.classify_core('O=C1c2ncccc2C(=O)c2ccccc21'), 'aza-9,10-AQ')

    def test_nn_filter(self):
        self.assertTrue(enum.has_nn('O=C1C=CC(=O)c2nnccc21'))
        self.assertFalse(enum.has_nn('O=C1C=CC(=O)c2nccnc21'))
        rows, stats = enum.enumerate_library(set(), limit=700)
        self.assertTrue(all(not enum.has_nn(r['smiles']) for r in rows))
        self.assertTrue(all(enum.classify_core(r['smiles']) == r['core'] for r in rows))

    def test_quota(self):
        self.assertEqual(subset.quotas({'a': 100, 'b': 25}, 30, 10), {'a': 20, 'b': 10})
        self.assertEqual(sum(subset.quotas({'a': 2, 'b': 100}, 30, 10).values()), 30)
        with self.assertRaises(ValueError): subset.quotas({'a': 20, 'b': 20}, 19, 10)

    def test_subset_determinism_and_size(self):
        rows, _ = enum.enumerate_library(set(), limit=40)
        a = subset.choose(rows, size=12, minimum=0, seed=7)
        b = subset.choose(list(reversed(rows)), size=12, minimum=0, seed=7)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 12)
        self.assertTrue(all(r['heavy_atoms'] <= 20 and r['estimated_gpu_seconds'] > 0 for r in a))
        self.assertEqual(len({r['inchikey'] for r in a}), 12)

    def test_tier1_accepts_subset_extra_columns_without_gpu(self):
        class Pool:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def starmap(self, fn, args):
                for arg in args: fn(*arg)
        class Context:
            def Pool(self, n): return Pool()
        def fake_worker(gpu, items, out):
            state = lambda energy: {'converged': True, 'geom_converged': True, 'error': None, 'energy': energy}
            for item in items:
                tier1.atomic_json(Path(out) / (item['inchikey'] + '.json'), {'states': {'Q_radical_anion': state(0), 'Q_dianion': state(-.09)}})
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); library = td / 'subset.csv'; common = td / 'common.json'
            library.write_text('smiles,inchikey,core,substituents,sa_score,heavy_atoms,estimated_gpu_seconds\nO=C1C=CC(=O)C=C1,TEST,1-4-BQ,H,2,8,123\n')
            state = lambda energy: {'converged': True, 'geom_converged': True, 'error': None, 'energy': energy}
            common.write_text(json.dumps({'states': {'O2': state(0), 'O2_radical_anion': state(-.08)}}))
            with patch.object(sys, 'argv', ['tier1', '--no-calib', '--library', str(library), '--out', str(td / 'out')]), \
                 patch.object(tier1, 'COMMON', common), patch.object(tier1.mp, 'get_context', return_value=Context()), \
                 patch.object(tier1, '_worker', fake_worker), redirect_stdout(io.StringIO()):
                tier1.main()
            with (td / 'out/tier1.csv').open() as handle: result = list(csv.DictReader(handle))
            self.assertEqual(result[0]['heavy_atoms'], '8')
            self.assertEqual(result[0]['survives'], 'True')
            meta = json.loads((td / 'out/tier1.csv.meta.json').read_text())
            self.assertEqual(meta['tolerance'], 0)

    def test_gate_defaults(self):
        s = 'O=C1C=CC(=O)C=C1'
        self.assertFalse(tier1.gate(s, -2.4, -2.3, None)['survives'])
        self.assertTrue(tier1.gate(s, -2.5, -2.3, None)['survives'])
        self.assertTrue(tier1.gate(s, -2.4, -2.3, None, .1)['survives'])

if __name__ == '__main__': unittest.main()
