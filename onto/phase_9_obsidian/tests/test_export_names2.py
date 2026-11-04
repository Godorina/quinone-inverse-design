"""KG names take precedence for merged compounds without losing aliases."""
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


def metadata(path):
    return {k: json.loads(v) for k, v in (line.split(': ', 1) for line in path.read_text().split('---\n', 2)[1].splitlines())}


class NamesTest(unittest.TestCase):
    def test_preferred_name(self):
        self.assertEqual(export.preferred_kg_name(['Anthraquinone', 'anthraquinone', '9,10-anthraquinone']), 'anthraquinone')
        self.assertEqual(export.preferred_kg_name(['anthraquinone', '9,10-anthraquinone']), '9,10-anthraquinone')
        self.assertEqual(export.preferred_kg_name(['long name', 'short']), 'short')
        self.assertEqual(export.preferred_kg_name(['Z', 'a']), 'a')

    def test_vault_name_aliases_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(structures, '_fetch', side_effect=AssertionError('network forbidden')):
                export.export(out)
            notes = list((out / 'Compounds').glob('*.md'))
            aq = next(p for p in notes if metadata(p).get('inchikey') == 'RZVHIXYEVGDQDX-UHFFFAOYSA-N')
            self.assertIn(aq.stem.casefold(), ('anthraquinone', '9,10-anthraquinone'))
            self.assertIn('unsubstituted AQ', metadata(aq)['aliases'])
            loop_only = [p for p in notes if metadata(p).get('source') == 'loop']
            self.assertTrue(loop_only)
            self.assertTrue(all(p.stem.startswith('Cand ') for p in loop_only))
            targets = {p.stem.casefold() for p in out.rglob('*.md')}
            targets.update(p.name.casefold() for p in (out / 'Structures').iterdir())
            for path in out.rglob('*.md'):
                for target in re.findall(r'\[\[([^\]]+)\]\]', path.read_text()):
                    self.assertIn(target.casefold(), targets, (path, target))


if __name__ == '__main__':
    unittest.main()
