"""Graph connectivity and verified Table 1 evidence, without network access."""
import csv
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


class GraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.out = cls.root / 'vault'
        cls.report = cls.root / 'unresolved.md'
        with patch.object(structures, '_fetch', side_effect=AssertionError('network forbidden')):
            export.export(cls.out, report_path=cls.report)
        cls.notes = list(cls.out.rglob('*.md'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_connectivity_and_static_index(self):
        targets = {p.stem.casefold(): p for p in self.notes}
        assets = {p.name.casefold() for p in (self.out / 'Structures').iterdir()}
        degree = {p: 0 for p in self.notes}
        for p in self.notes:
            for target in re.findall(r'\[\[([^\]]+)\]\]', p.read_text()):
                key = target.casefold()
                self.assertTrue(key in targets or key in assets, (p, target))
                if key in targets:
                    degree[p] += 1
                    degree[targets[key]] += 1
        self.assertFalse([p for p, count in degree.items() if not count])
        index = (self.out / 'Index.md').read_text()
        readme = (self.out / 'README.md').read_text()
        self.assertIn('[[Index]]', readme)
        for p in (self.out / 'Families').glob('*.md'):
            self.assertIn('[[' + p.stem + ']]', readme)
            self.assertIn('[[' + p.stem + ']]', index)
        for folder in ('Papers', 'Runs'):
            for p in (self.out / folder).glob('*.md'):
                self.assertIn('[[' + p.stem + ']]', index)
        ranking = index.split('## Top 10 compounds (static)\n', 1)[1].split('\n## ', 1)[0]
        ranked = re.findall(r'\[\[([^\]]+)\]\]', ranking)
        eligible = [(meta(p)['f_v2'], p.stem) for p in (self.out / 'Compounds').glob('*.md') if meta(p).get('f_v2') is not None and meta(p).get('co2_detached') is False]
        expected = [name for _, name in sorted(eligible, key=lambda x: (-x[0], x[1].casefold(), x[1]))[:10]]
        self.assertEqual(ranked, expected)

    def test_table_and_empty_papers(self):
        papers = {meta(p)['doi']: p for p in (self.out / 'Papers').glob('*.md')}
        paper = papers['10.1021/acs.jpcc.2c03752']
        text = paper.read_text()
        with (ROOT / 'onto/phase_4b_extend/alherz2022_table1.csv').open() as f:
            rows = [row for row in csv.DictReader(f) if row['inchikey']]
        notes = {meta(p).get('inchikey'): p for p in (self.out / 'Compounds').glob('*.md')}
        for row in rows:
            note = notes[row['inchikey']]
            self.assertIn('[[' + note.stem + ']]', text)
            section = note.read_text().split('## Alherz 2022 Table 1 measurements', 1)[1].split('\n## ', 1)[0]
            self.assertIn('[[' + paper.stem + ']]', section)
            self.assertIn(row['exp_E2_V'], section)
            if row['exp_dG_bind_kcal']:
                self.assertIn(row['exp_dG_bind_kcal'], section)
            self.assertIn('Table 1, PDF image entry, independently checked', section)
        for doi in ('10.1002/cphc.202500472', '10.1002/cssc.202401315'):
            p = papers[doi]
            self.assertIn('No compound extracted from this paper (needs review)', p.read_text())
            self.assertIn(doi, self.report.read_text())
        self.assertNotIn('Table 1, PDF image entry, independently checked', papers['10.1002/cphc.202500472'].read_text())

    def test_deterministic(self):
        other = self.root / 'other'
        report = self.root / 'other.md'
        with patch.object(structures, '_fetch', side_effect=AssertionError('network forbidden')):
            export.export(other, report_path=report)
        for p in self.out.rglob('*.md'):
            self.assertEqual(p.read_bytes(), (other / p.relative_to(self.out)).read_bytes(), p)
        self.assertEqual(self.report.read_bytes(), report.read_bytes())


if __name__ == '__main__':
    unittest.main()
