"""Conservative reference-name matching and cached PubChem variants."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export
import structures


def meta(path):
    return {k: json.loads(v) for k, v in (line.split(': ', 1) for line in path.read_text().split('---\n', 2)[1].splitlines())}


class ResolutionTest(unittest.TestCase):
    def test_variants_and_guards(self):
        variants = structures.name_variants('2,3-dichloro-p-napthoquinone (cpd-m062)')
        self.assertIn('2,3-dichloro-p-naphthoquinone', variants)
        self.assertIn('2,3-dichloro-1,4-naphthoquinone', variants)
        self.assertIn('9,10-anthraquinone', structures.name_variants('anthra-quinone'))
        for name in ('poly(anthraquinone)', 'Ru(bpy)2(phendione) 2+', 'ester derivative of 9,10-anthraquinone', 'anthraquinone sodium salt', 'BDT-Q/CNT', 'PBDT-Q', 'chitosan−rhenium', 'anthraquinone-2,7-disulfonate (AQDS)'):
            self.assertIsNotNone(structures.name_guard(name), name)

    def test_reference_index_and_ambiguity(self):
        index = structures.reference_names(ROOT)
        hit = structures.reference_match('benzodithiophene quinone (BDT-Q)', index)
        self.assertEqual(hit['inchikey'], 'SIUXRPJYVQQBAF-UHFFFAOYSA-N')
        self.assertEqual(hit['status'], 'reference-name')
        self.assertIsNone(structures.reference_match('poly(anthraquinone)', index))
        self.assertIsNone(structures.reference_match('benzodithiophene quinone (BDT-Q)', {'bdtq': {'A': 'a', 'B': 'b'}}))

    def test_bdt_merge_and_cache_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(structures, '_fetch', side_effect=AssertionError('network forbidden')):
                export.export(out)
            matches = [p for p in (out / 'Compounds').glob('*.md') if meta(p).get('inchikey') == 'SIUXRPJYVQQBAF-UHFFFAOYSA-N']
            self.assertEqual(len(matches), 1)
            text = matches[0].read_text()
            self.assertIn('benzodithiophene quinone (BDT-Q)', meta(matches[0])['aliases'])
            self.assertIn('reference-name', text)
            self.assertIn('## Structure', text)
            self.assertIn('DFT B3LYP/def2-SVP', text)
            self.assertTrue((out / 'Structures' / (matches[0].stem + ' + CO2.xyz')).exists())
            names = {p.stem.casefold() for p in out.rglob('*.md')} | {p.name.casefold() for p in (out / 'Structures').iterdir()}
            for note in out.rglob('*.md'):
                for link in re.findall(r'\[\[([^\]]+)\]\]', note.read_text()):
                    self.assertIn(link.casefold(), names, (note, link))


if __name__ == '__main__':
    unittest.main()
