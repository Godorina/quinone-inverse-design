"""Regression tests for vault preservation, identity and navigation."""
import csv
import json
import re
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, Namespace, RDF
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export

QN = Namespace('https://w3id.org/quinone#')


def metadata(path):
    return {k: json.loads(v) for k, v in (line.split(': ', 1) for line in path.read_text().split('---\n', 2)[1].splitlines())}


class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / 'vault'
        (cls.out / '.obsidian').mkdir(parents=True)
        (cls.out / '.obsidian/app.json').write_text('{"settings": true}')
        (cls.out / 'personal.md').write_text('my own note')
        (cls.out / 'Custom').mkdir()
        (cls.out / 'Custom' / 'keep.txt').write_text('keep')
        (cls.out / 'Papers').mkdir()
        (cls.out / 'Papers' / 'stale.md').write_text('old')
        export.export(cls.out)
        cls.compounds = list((cls.out / 'Compounds').glob('*.md'))
        cls.graph = Graph().parse(ROOT / 'onto/phase_5_build/kg.ttl')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_user_files_preserved_and_stale_output_removed(self):
        self.assertEqual((self.out / '.obsidian/app.json').read_text(), '{"settings": true}')
        self.assertEqual((self.out / 'personal.md').read_text(), 'my own note')
        self.assertEqual((self.out / 'Custom/keep.txt').read_text(), 'keep')
        self.assertFalse((self.out / 'Papers/stale.md').exists())

    def test_generated_symlink_does_not_delete_its_target(self):
        target = Path(self.tmp.name) / 'other-files'
        target.mkdir(exist_ok=True)
        (target / 'keep.txt').write_text('keep')
        output = Path(self.tmp.name) / 'symlink-vault'
        output.mkdir(exist_ok=True)
        (output / 'Families').symlink_to(target, target_is_directory=True)
        export.export(output)
        self.assertEqual((target / 'keep.txt').read_text(), 'keep')
        self.assertFalse((output / 'Families').is_symlink())

    def test_zero_values_are_not_erased(self):
        self.assertEqual(export.cell(0), '0')
        self.assertEqual(export.cell(False), 'False')

    def test_inchikey_merged_with_all_evidence(self):
        key_nodes = {}
        references = export.structures.reference_names(ROOT)
        schema = Namespace('https://schema.org/')
        for c in self.graph.subjects(RDF.type, QN.Compound):
            key = self.graph.value(c, QN.inchikey)
            smiles = self.graph.value(c, QN.smiles)
            if not smiles:
                name = str(self.graph.value(c, schema.name) or '')
                resolved = (export.structures.reference_match(name, references)
                            or export.structures.resolve_variants(name, online=False))
                smiles = resolved.get('smiles')
            if smiles:
                molecule = Chem.MolFromSmiles(str(smiles))
                if molecule:
                    key = Chem.MolToInchiKey(molecule)
            if key:
                key_nodes.setdefault(str(key), []).append(c)
        self.assertGreaterEqual(sum(len(v) > 1 for v in key_nodes.values()), 2)
        keys = [metadata(p).get('inchikey') for p in self.compounds if metadata(p).get('inchikey')]
        self.assertEqual(len(keys), len(set(keys)))
        for key, nodes in key_nodes.items():
            if len(nodes) < 2:
                continue
            note = next(p for p in self.compounds if metadata(p).get('inchikey') == key)
            expected = sum(1 for n in nodes for r in self.graph.subjects(QN.ofCompound, n)
                           if self.graph.value(self.graph.value(r, QN.hasEvidence), QN.quote))
            self.assertEqual(sum(line.startswith('> ') for line in note.read_text().splitlines()), expected)

    def test_names_aliases_families_and_all_links(self):
        files = list(self.out.rglob('*.md'))
        names = {p.stem.casefold() for p in files} | {p.name.casefold() for p in (self.out / 'Structures').iterdir() if p.is_file()}
        for p in files:
            self.assertNotRegex(p.stem, r' - [a-f0-9]{12}$')
            for target in re.findall(r'\[\[([^\]]+)\]\]', p.read_text()):
                self.assertIn(target.casefold(), names)
        family_names = {p.stem for p in (self.out / 'Families').glob('*.md')}
        self.assertTrue(family_names)
        for p in self.compounds:
            data = metadata(p)
            aliases = data['aliases']
            for key in ('inchikey', 'smiles'):
                if data.get(key):
                    self.assertIn(data[key], aliases)
            targets = re.findall(r'\[\[([^\]]+)\]\]', p.read_text())
            self.assertTrue(family_names.intersection(targets), p)
        for p in (self.out / 'Families').glob('*.md'):
            self.assertIn('[[', p.read_text())

    def test_detached_flags_and_index_queries(self):
        d = {metadata(p).get('inchikey'): metadata(p) for p in self.compounds}
        self.assertIs(d['DNXUGBMARDFRGG-UHFFFAOYSA-N']['co2_detached'], True)
        self.assertIs(d['METHVWQPJYOAPU-UHFFFAOYSA-N']['co2_detached'], False)
        self.assertIn('highlevel_flags', d['METHVWQPJYOAPU-UHFFFAOYSA-N'])
        self.assertIn('loop-20261102-212436', d['METHVWQPJYOAPU-UHFFFAOYSA-N']['runs'])
        index = (self.out / 'Index.md').read_text()
        self.assertGreaterEqual(index.count('!co2_detached'), 2)
        self.assertIn('GROUP BY run', index)
        self.assertIn('FLATTEN runs AS run', index)
        self.assertIn('GROUP BY year', index)

    def test_round_specific_citations_and_highlevel_only(self):
        root = Path(self.tmp.name) / 'fixture'
        (root / 'onto').mkdir(parents=True)
        for name in ('phase_5_build', 'phase_2_schema', 'phase_4b_extend'):
            (root / 'onto' / name).symlink_to(ROOT / 'onto' / name, target_is_directory=True)
        runs = root / 'onto/phase_8_design/runs/loop-fixture'
        (runs / 'round_1').mkdir(parents=True)
        (runs / 'round_2').mkdir()
        ref = root / 'dft/runs/ref_set'
        ref.parent.mkdir(parents=True)
        ref.symlink_to(ROOT / 'dft/runs/ref_set', target_is_directory=True)
        (ref.parent / 'highlevel_fixture').mkdir()
        (ref.parent / 'highlevel_fixture/summary.json').write_text(json.dumps({'molecules': [{'id': 'ONLYHIGH-KEY', 'smiles': 'onlyhigh', 'flags': ['imag:Q:1']}]}))
        data = {'inchikey': 'LOOPFIX-KEY', 'smiles': 'loopfix', 'E2_eV': 1, 'dE_bind_kcal': -1, 'margin': .3, 'co2_detached': False, 'cited_ids': ['D99']}
        (runs / 'ledger.jsonl').write_text(json.dumps({'round': 2, 'arm': 'llm', 'results': [data]}) + '\n')
        (runs / 'round_1/prompt_1.txt').write_text('No relevant evidence\n')
        refdata = json.loads((ROOT / 'dft/runs/ref_set/GHLUWAJFYKILGZ-UHFFFAOYSA-N.json').read_text())
        (runs / 'round_2/prompt.txt').write_text(f"D99 {refdata['smiles']} E2=-2.0\n")
        fixture_out = Path(self.tmp.name) / 'fixture-vault'
        with patch.object(export, 'ROOT', root):
            export.export(fixture_out)
        notes = list((fixture_out / 'Compounds').glob('*.md'))
        loop = next(p for p in notes if metadata(p).get('inchikey') == 'LOOPFIX-KEY')
        high = next(p for p in notes if metadata(p).get('inchikey') == 'ONLYHIGH-KEY')
        self.assertRegex(loop.read_text(), r'D99: \[\[[^\]]+\]\]')
        self.assertEqual(metadata(high)['source'], 'highlevel')
        self.assertIn('imag:Q:1', metadata(high)['highlevel_flags'])


if __name__ == '__main__':
    unittest.main()
