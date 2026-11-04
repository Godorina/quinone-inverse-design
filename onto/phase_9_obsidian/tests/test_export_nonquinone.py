import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export
import structures

BTZ = 'c1ccc2nsnc2c1'
BQ = 'O=C1C=CC(=O)C=C1'


def response(smiles, cid=7):
    return {'PropertyTable': {'Properties': [{'CID': cid, 'Title': 'name', 'SMILES': smiles}]}}


class NonQuinoneTests(unittest.TestCase):
    def test_stale_cache_requery_and_offline(self):
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / 'cache.json'
            cache.write_text(json.dumps({'BTZ': {'status': 'not_quinone'}}))
            with patch.object(structures, 'NAME_CACHE', cache), patch.object(structures.time, 'sleep'):
                self.assertEqual(structures.resolve_name('BTZ', online=False)['status'], 'not_quinone')
                result = structures.resolve_name('BTZ', fetch=lambda *_a, **_kw: response(BTZ))
                self.assertEqual(result['status'], 'found')
                self.assertEqual(json.loads(cache.read_text())['BTZ']['smiles'], BTZ)
                self.assertEqual(structures.resolve_name('BTZ', fetch=lambda *_a, **_kw: self.fail('unexpected network')), result)

    def test_oversize_cache_is_rechecked_once_for_new_limit(self):
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / 'cache.json'
            cache.write_text(json.dumps({'old': {'status': 'too_many_heavy_atoms'}}))
            with patch.object(structures, 'NAME_CACHE', cache), patch.object(structures.time, 'sleep'):
                self.assertEqual(structures.resolve_name('old', fetch=lambda *_a, **_kw: response('C' * 41))['status'], 'too_many_heavy_atoms')
                self.assertEqual(json.loads(cache.read_text())['old']['max_heavy_atoms'], 40)
                self.assertEqual(structures.resolve_name('old', fetch=lambda *_a, **_kw: self.fail('unexpected network'))['status'], 'too_many_heavy_atoms')

    def test_reject_salts_metals_large_and_ambiguous(self):
        with tempfile.TemporaryDirectory() as td, patch.object(structures, 'NAME_CACHE', Path(td) / 'cache'), patch.object(structures.time, 'sleep'):
            for name, smiles, status in [('salt', 'C.[Na+]', 'charged_or_disconnected'),
                                         ('metallic', 'C[Fe]', 'metal'), ('large', 'C' * 41, 'too_many_heavy_atoms'),
                                         ('inorganic', 'O', 'not_organic'), ('invalid', 'nonsense', 'invalid_smiles')]:
                # Avoid the name guard on the test label itself.
                self.assertEqual(structures.resolve_name('test ' + status, fetch=lambda *_a, **_kw: response(smiles))['status'], status)
            multiple = {'PropertyTable': {'Properties': [{'CID': 1, 'Title': 'test multiple', 'SMILES': BQ}, {'CID': 2, 'Title': 'other', 'SMILES': BTZ}]}}
            self.assertEqual(structures.resolve_name('test multiple', fetch=lambda *_a, **_kw: multiple)['status'], 'ambiguous')

    def test_limits_and_ring_check_are_independent(self):
        self.assertIsNone(structures.display_rejection('C' * 40))
        self.assertEqual(structures.display_rejection('C' * 41), 'too_many_heavy_atoms')
        self.assertFalse(structures.is_quinone(BTZ))
        self.assertTrue(structures.is_quinone(BQ))
        # A large quinone exceeds the design limit but retains its chemical ring label.
        big = 'O=C1C(' + 'C' * 25 + ')=CC(=O)C=C1'
        self.assertIsNone(structures.display_rejection(big))
        self.assertTrue(structures.is_quinone(big))

    def test_structure_and_mismatch_in_vault(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); cache = td / 'cache.json'
            original = json.loads(structures.NAME_CACHE.read_text())
            original['2,1,3-benzothiadiazole'] = {'status': 'found', 'cid': 67499, 'smiles': BTZ}
            cache.write_text(json.dumps(original))
            with patch.object(structures, 'NAME_CACHE', cache):
                export.export(td / 'vault')
            notes = list((td / 'vault/Compounds').glob('2,1,3-benzothiadiazole (BTZ)*'))
            self.assertEqual(len(notes), 1)
            text = notes[0].read_text()
            meta = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in text.split('---\n', 2)[1].splitlines())}
            self.assertEqual(meta['quinone'], False)
            self.assertEqual(meta['skeleton_check'], 'mismatch')
            self.assertEqual(meta['skeleton'], 'HeterocyclicQuinone')
            self.assertIn('Not a quinone (outside the design domain)', text)
            self.assertTrue((td / 'vault/Structures' / (notes[0].stem + '.xyz')).exists())
            self.assertTrue((td / 'vault/Structures' / (notes[0].stem + '.png')).exists())

if __name__ == '__main__': unittest.main()
