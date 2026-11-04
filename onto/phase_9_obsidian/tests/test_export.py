"""Offline integration contracts for the generated Obsidian vault."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export

QN = Namespace('https://w3id.org/quinone#')


def frontmatter(text):
    parts = text.split('---\n', 2)
    assert len(parts) == 3 and parts[0] == ''
    return {key: json.loads(value) for key, value in
            (line.split(': ', 1) for line in parts[1].splitlines())}


class VaultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.a, cls.b = cls.root / 'a', cls.root / 'b'
        export.export(cls.a)
        export.export(cls.b)
        cls.files = sorted(cls.a.rglob('*.md'))
        cls.graph = Graph().parse(ROOT / 'onto/phase_5_build/kg.ttl', format='turtle')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_counts_and_frontmatter(self):
        papers = list((self.a / 'Papers').glob('*.md'))
        compounds = list((self.a / 'Compounds').glob('*.md'))
        self.assertEqual(len(papers), len(set(self.graph.subjects(RDF.type, QN.Paper))))
        self.assertGreaterEqual(len(compounds), len(set(self.graph.subjects(RDF.type, QN.Compound))))
        for path in papers + compounds + list((self.a / 'Runs').glob('*.md')):
            data = frontmatter(path.read_text())
            self.assertIn(data['type'], ('paper', 'compound', 'run'))

    def test_all_wikilinks_resolve_and_names_are_safe(self):
        names = [p.stem.casefold() for p in self.files]
        self.assertEqual(len(names), len(set(names)))
        names += [p.name.casefold() for p in (self.a / 'Structures').iterdir() if p.is_file()]
        for path in self.files:
            self.assertNotRegex(path.name, r'[/\\:*?"<>|#\^\[\]]')
            for target in re.findall(r'\[\[([^\]]+)\]\]', path.read_text()):
                self.assertIn(target.casefold(), names, (path, target))

    def test_quotes_are_limited_and_from_graph(self):
        originals = {str(q) for q in self.graph.objects(None, QN.quote)}
        seen = 0
        for path in (self.a / 'Compounds').glob('*.md'):
            for line in path.read_text().splitlines():
                if line.startswith('> '):
                    quote = line[2:]
                    self.assertLessEqual(len(quote), 200)
                    self.assertTrue(any(' '.join(x.split()).startswith(quote.rstrip('…')) for x in originals), quote)
                    seen += 1
        self.assertGreater(seen, 0)

    def test_determinism(self):
        def contents(root):
            return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertEqual(contents(self.a), contents(self.b))
        for seed in ('1', '2'):
            target = self.root / ('seed-' + seed)
            code = 'import sys; sys.path.insert(0, sys.argv[1]); import export; export.export(sys.argv[2])'
            subprocess.run([sys.executable, '-c', code, str(ROOT / 'onto/phase_9_obsidian'), str(target)],
                           check=True, env={**os.environ, 'PYTHONHASHSEED': seed})
            self.assertEqual(contents(self.a), contents(target))

    def test_make_target_runs_even_after_vault_exists(self):
        result = subprocess.run(['make', '-n', 'obsidian'], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertIn('phase_9_obsidian/export.py', result.stdout)

    def test_known_loop_candidate_has_scores_and_history(self):
        smiles = 'O=C1C=CC(=O)c2nc3cnc(F)cc3nc21'
        hits = [(p, frontmatter(p.read_text())) for p in (self.a / 'Compounds').glob('*.md')
                if frontmatter(p.read_text()).get('smiles') == smiles]
        self.assertTrue(hits)
        self.assertTrue(any(data.get('f_v2') is not None and data.get('o2_margin_V') is not None
                            and 'loop-20261102-212436' in p.read_text() for p, data in hits))

    def test_paper_measurements_and_highlevel_provenance(self):
        self.assertTrue(any(any(line.startswith('| [[') for line in p.read_text().splitlines())
                            for p in (self.a / 'Papers').glob('*.md')))
        self.assertTrue(any(any(line.startswith('| ') and ' [[' in line for line in p.read_text().splitlines())
                            for p in (self.a / 'Runs').glob('*.md')))
        self.assertTrue(any('High-level' in p.read_text() and 'dG_bind_1M_kcal' in p.read_text()
                            for p in (self.a / 'Compounds').glob('*.md')))


if __name__ == '__main__':
    unittest.main()
