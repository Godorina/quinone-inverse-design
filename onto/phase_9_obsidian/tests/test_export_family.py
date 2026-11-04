"""Structure-derived family assignment and vault navigation, without calculations."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export


def meta(path):
    return {key: json.loads(value) for key, value in
            (line.split(': ', 1) for line in path.read_text().split('---\n', 2)[1].splitlines())}


class SkeletonTest(unittest.TestCase):
    def test_quinone_fused_ring_systems(self):
        examples = {
            'O=C1C=CC(=O)C=C1': 'Benzoquinone',
            'O=C1C(Cl)=CC(=O)C(Cl)=C1': 'Benzoquinone',
            'O=C1C=CC(=O)c2ccccc21': 'Naphthoquinone',
            'O=C1c2ccccc2C(=O)c2ccccc21': 'Anthraquinone',
            'O=C1C(=O)c2ccccc2-c2ccccc21': 'Phenanthrenequinone',
            'O=C1C=CC(=O)c2nccnc21': 'HeterocyclicQuinone',
            'O=C1C=CC(=O)c2nc3cnc(F)cc3nc21': 'HeterocyclicQuinone',
            'O=C1c2ccsc2C(=O)c2ccsc21': 'HeterocyclicQuinone',
            'O=C1C=CC(=O)c2ccc3cc4ccccc4cc3c21': 'OtherQuinoid',
        }
        for smiles, expected in examples.items():
            with self.subTest(smiles=smiles):
                self.assertEqual(export.skeleton_from_smiles(smiles), expected)

    def test_substituent_rings_are_not_fused(self):
        self.assertEqual(export.skeleton_from_smiles('O=C1C(-c2nccnc2)=CC(=O)C=C1'), 'Benzoquinone')
        self.assertEqual(export.skeleton_from_smiles('O=C1C([N+](=O)[O-])=CC(=O)C=C1'), 'Benzoquinone')

    def test_unknown_and_nonquinone_are_not_misclassified(self):
        for smiles in (None, '', 'c1ccccc1', 'O=C1CCC(=O)CC1', 'O=C1CC(=O)c2ccccc21'):
            with self.subTest(smiles=smiles):
                self.assertEqual(export.skeleton_from_smiles(smiles), 'NotReported')

    def test_vault_has_no_unclassified_and_finer_hubs_link_to_skeletons(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'vault'
            export.export(out)
            notes = list(out.rglob('*.md'))
            names = {p.stem for p in notes} | {p.name for p in (out / 'Structures').iterdir() if p.is_file()}
            self.assertFalse((out / 'Families/Unclassified.md').exists())
            self.assertFalse((out / 'Families/Benzoquinone (family) (family).md').exists())
            self.assertFalse((out / 'Families/Anthraquinone (family) (family).md').exists())
            for path in (out / 'Compounds').glob('*.md'):
                self.assertNotIn('[[Unclassified]]', path.read_text(), path)
                for target in re.findall(r'\[\[([^\]]+)\]\]', path.read_text()):
                    self.assertIn(target, names)
            key = 'METHVWQPJYOAPU-UHFFFAOYSA-N'
            candidate = next(p for p in (out / 'Compounds').glob('*.md') if meta(p).get('inchikey') == key)
            self.assertEqual(meta(candidate)['skeleton'], 'HeterocyclicQuinone')
            self.assertIn('[[HeterocyclicQuinone]]', candidate.read_text())
            benzo = [p for p in (out / 'Compounds').glob('*.md') if meta(p).get('source') == 'loop' and meta(p).get('skeleton') == 'Benzoquinone']
            self.assertTrue(benzo)
            self.assertTrue(all('[[Benzoquinone (family)]]' in p.read_text() for p in benzo))
            for family, expected in [('quinoxaline-dione', 'HeterocyclicQuinone'),
                                     ('benzodithiophene-dione', 'HeterocyclicQuinone'),
                                     ('diaminonaphthoquinone', 'Naphthoquinone')]:
                hub = out / 'Families' / (family + '.md')
                self.assertIn(f'Skeleton: [[{expected}]]', hub.read_text())
                for target in re.findall(r'\[\[([^\]]+)\]\]', hub.read_text()):
                    self.assertIn(target, names)
            reference = next(p for p in (out / 'Compounds').glob('*.md') if meta(p).get('inchikey') == 'SIUXRPJYVQQBAF-UHFFFAOYSA-N')
            self.assertEqual(meta(reference)['skeleton'], 'HeterocyclicQuinone')
            self.assertIn('[[benzodithiophene-dione]]', reference.read_text())


if __name__ == '__main__':
    unittest.main()
