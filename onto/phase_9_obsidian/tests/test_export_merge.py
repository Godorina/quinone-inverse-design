"""Structure identity and evidence conservation, using only local data."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, Namespace, RDF
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'onto/phase_9_obsidian'))
import export
import structures
QN = Namespace('https://w3id.org/quinone#')


def meta(path):
    return {k: json.loads(v) for k, v in (line.split(': ', 1) for line in path.read_text().split('---\n', 2)[1].splitlines())}


class MergeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / 'vault'
        with patch.object(structures, '_fetch', side_effect=AssertionError('network forbidden')):
            export.export(cls.out)
        cls.notes = list((cls.out / 'Compounds').glob('*.md'))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_keys_unique_and_derived(self):
        entries = [meta(p) for p in self.notes]
        keys = [x['inchikey'] for x in entries if x.get('inchikey')]
        self.assertEqual(len(keys), len(set(keys)))
        for item in entries:
            if item.get('smiles'):
                self.assertEqual(item['inchikey'], Chem.MolToInchiKey(Chem.MolFromSmiles(item['smiles'])))

    def test_names_merged_and_aliases(self):
        examples = [('anthraquinone', '9,10-anthraquinone'), ('benzoquinone', 'p-Benzoquinone'),
                    ('phendione', '1,10-phenanthroline-5,6-dione'), ('Vitamin K3', '2-methyl-1,4-naphthoquinone'),
                    ('Bromanil', 'tetrabromo-p-benzoquinone')]
        for first, second in examples:
            hits = [(p, meta(p)) for p in self.notes if first.casefold() in {v.casefold() for v in meta(p)['aliases']} and second.casefold() in {v.casefold() for v in meta(p)['aliases']}]
            self.assertEqual(len(hits), 1, (first, second, hits))
            self.assertIn('Also reported as:', hits[0][0].read_text())

    def test_reference_title_and_family_members_are_unique(self):
        aq = next(p for p in self.notes if meta(p).get('inchikey') == 'RZVHIXYEVGDQDX-UHFFFAOYSA-N')
        self.assertEqual(aq.stem, 'anthraquinone')
        self.assertIn('9,10-anthraquinone', meta(aq)['pubchem_name_unverified'])
        for hub in (self.out / 'Families').glob('*.md'):
            members = re.findall(r'^- \[\[([^\]]+)\]\]', hub.read_text(), re.M)
            self.assertEqual(len(members), len(set(members)), hub)

    def test_measurements_and_links(self):
        graph = Graph().parse(ROOT / 'onto/phase_5_build/kg.ttl')
        compounds = set(graph.subjects(RDF.type, QN.Compound))
        expected = sum(1 for t in (QN.Measurement, QN.Observation) for x in set(graph.subjects(RDF.type, t)) if graph.value(x, QN.ofCompound) in compounds)
        actual = 0
        for p in self.notes:
            section = p.read_text().split('## Literature measurements and observations\n', 1)[1].split('\n## ', 1)[0]
            actual += sum(line.startswith('- [[') or line.startswith('- unknown paper:') for line in section.splitlines())
        self.assertEqual(actual, expected)
        names = {p.stem.casefold() for p in self.out.rglob('*.md')}
        names |= {p.name.casefold() for p in (self.out / 'Structures').iterdir()}
        for path in self.out.rglob('*.md'):
            for target in re.findall(r'\[\[([^\]]+)\]\]', path.read_text()):
                self.assertIn(target.casefold(), names, (path, target))


if __name__ == '__main__':
    unittest.main()
