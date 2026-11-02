import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from rdflib import Graph, Literal, RDF, RDFS, OWL, Namespace
from rdflib.namespace import XSD

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
QN = Namespace('https://w3id.org/quinone#')


def test_schema_and_build():
    schema = Graph().parse(build.ONTO / 'phase_2_schema/schema/quinone.ttl')
    assert (QN.pubchemCID, RDF.type, OWL.DatatypeProperty) in schema
    assert (QN.pubchemCID, RDFS.domain, QN.Compound) in schema
    assert (QN.pubchemCID, RDFS.range, XSD.integer) in schema
    assert {x.language for x in schema.objects(QN.pubchemCID, RDFS.label)} >= {'ko', 'en'}
    assert {x.language for x in schema.objects(QN.pubchemCID, RDFS.comment)} >= {'ko', 'en'}
    original = Graph().parse(data=build.build(), format='turtle')
    subject, key = next(original.subject_objects(QN.inchikey))
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / 'cache.json'
        cache.write_text(json.dumps({str(key): {'cid': 123, 'iupac': None, 'status': 'found'}}))
        with patch.object(build, 'PUBCHEM_CACHE', cache):
            ttl = build.build()
            assert ttl == build.build()
        graph = Graph().parse(data=ttl, format='turtle')
        assert (subject, QN.pubchemCID, Literal(123, datatype=XSD.integer)) in graph


if __name__ == '__main__':
    test_schema_and_build()
    print('pubchem build tests passed')
