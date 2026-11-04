"""Offline contracts for 2D/3D structure assets and conservative name lookup."""
import json
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export
import structures

BQ = 'O=C1C=CC(=O)C=C1'


class StructuresTest(unittest.TestCase):
    def test_name_lookup_rules_and_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / 'names.json'
            def fetch(url, timeout):
                return {'PropertyTable': {'Properties': [{'CID': 1, 'Title': 'p-Benzoquinone', 'SMILES': BQ}]}}
            with patch.object(structures, 'NAME_CACHE', cache):
                self.assertEqual(structures.resolve_name('polymer resin', fetch=fetch)['status'], 'material')
                self.assertEqual(structures.resolve_name('naphthoquinone dianion', fetch=fetch)['status'], 'material')
                resolved = structures.resolve_name('p-Benzoquinone', fetch=fetch)
                self.assertEqual(resolved['smiles'], BQ)
                self.assertEqual(structures.resolve_name('p-Benzoquinone', fetch=lambda *_a, **_k: self.fail('cached lookup')), resolved)
                many = lambda *_a, **_k: {'PropertyTable': {'Properties': [{'CID': 1, 'Title': 'different', 'SMILES': BQ}, {'CID': 2, 'Title': 'other', 'SMILES': BQ}]}}
                self.assertEqual(structures.resolve_name('ambiguous', fetch=many)['status'], 'ambiguous')
                wrong = lambda *_a, **_k: {'PropertyTable': {'Properties': [{'CID': 3, 'Title': 'benzene', 'SMILES': 'c1ccccc1'}]}}
                benzene = structures.resolve_name('benzene', fetch=wrong)
                self.assertEqual(benzene['status'], 'found')
                self.assertEqual(benzene['smiles'], 'c1ccccc1')
                self.assertFalse(structures.is_quinone(benzene['smiles']))

    def test_geometry_precedence_and_attachment(self):
        low = {'states': {'Q': {'converged': True, 'geom_converged': True, 'xyz': '2\nold\nC 0 0 0\nO 1 0 0\n'}}, 'adducts': {}}
        high = {'status': 'ok', 'opt_converged': True, 'xyz_final': 'C 0 0 0\nO 2 0 0'}
        xyz, source = structures.geometry(BQ, low, high)
        self.assertTrue(xyz.startswith('2\nωB97M-V/def2-TZVPD\n'))
        self.assertIn('2 0 0', xyz)
        xyz, source = structures.geometry(BQ, low, None)
        self.assertIn('DFT B3LYP/def2-SVP', xyz)
        xyz, source = structures.geometry(BQ, None, None)
        self.assertIn('RDKit/MMFF (not DFT)', xyz)
        detached = {'converged': True, 'geom_converged': True, 'energy': -10, 'o_index': 0, 'xyz': '4\n\nO 0 0 0\nC 5 0 0\nO 6 0 0\nO 4 0 0\n'}
        self.assertIsNone(structures.attached_adduct({'adducts': {'x': detached}}))
        attached = {**detached, 'energy': -9, 'xyz': detached['xyz'].replace('C 5 0 0', 'C 1.5 0 0')}
        self.assertEqual(structures.attached_adduct({'adducts': {'x': detached, 'y': attached}})['energy'], -9)

    def test_vault_assets_and_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / '.obsidian').mkdir()
            (out / '.obsidian' / 'settings').write_text('keep')
            export.export(out)
            notes = list((out / 'Compounds').glob('*.md'))
            for note in notes:
                text = note.read_text()
                meta = {k: json.loads(v) for k, v in (line.split(': ', 1) for line in text.split('---\n', 2)[1].splitlines())}
                if meta.get('smiles'):
                    for ext in ('png', 'xyz'):
                        target = note.stem + '.' + ext
                        self.assertIn('![[' + target + ']]', text)
                        self.assertTrue((out / 'Structures' / target).is_file(), target)
            targets = {path.stem.casefold() for path in out.rglob('*.md')}
            targets |= {path.name.casefold() for path in (out / 'Structures').iterdir()}
            for note in out.rglob('*.md'):
                for target in re.findall(r'\[\[([^\]]+)\]\]', note.read_text()):
                    self.assertIn(target.casefold(), targets, (note, target))
            for path in (out / 'Structures').glob('*.png'):
                self.assertEqual(struct.unpack('>II', path.read_bytes()[16:24]), (300, 300))
            with patch.object(structures, '_fetch', side_effect=AssertionError('offline export used network')):
                second = out / 'second-vault'
                export.export(second)
            for folder in ('Compounds', 'Structures', 'Papers', 'Runs', 'Families'):
                first_files = {p.name: p.read_bytes() for p in (out / folder).iterdir() if p.is_file()}
                second_files = {p.name: p.read_bytes() for p in (second / folder).iterdir() if p.is_file()}
                self.assertEqual(first_files, second_files, folder)
            self.assertEqual((out / '.obsidian' / 'settings').read_text(), 'keep')
            self.assertIn('ChemRender3D', (out / 'README.md').read_text())
            self.assertTrue(list((out / 'Structures').glob('* + CO2.xyz')))


if __name__ == '__main__':
    unittest.main()
