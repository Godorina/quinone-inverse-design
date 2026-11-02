"""quinone ontology checks (electrochemical CO2 capture with quinones).
Run (from this folder): /home/hgpark/whlee/hgpark/mlp-icl-llmsr/.venv/bin/python tests/test_onto.py"""
import json
import sys
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Namespace, URIRef
from rdflib.namespace import SKOS

ONTO = Path(__file__).resolve().parents[1]
CHECK = next(p / "al_alloy" / "common" for p in ONTO.parents if (p / "al_alloy" / "common" / "check.py").is_file())
sys.path.insert(0, str(CHECK))
from check import schema_files, tools  # noqa: E402

QN = Namespace("https://w3id.org/quinone#")
check, cq = tools(ONTO)
EXAMPLES = sorted((ONTO / "examples").glob("*.ttl"))
MUST_HAVE = {"cq01", "cq02", "cq04", "cq05", "cq07", "cq08", "cq13", "cq14", "cq19", "cq20", "cq22"}  # phase_1_scope/cq.md
DATA = ONTO.parent / "data" / "on_topic_final.json"


def schema() -> Graph:
    g = Graph()
    for f in schema_files(ONTO):
        g.parse(f)
    return g


def qn_terms(g, kind):
    return {s for s in g.subjects(RDF.type, kind) if str(s).startswith(str(QN))}


def test_classes_are_exactly_the_planned_ones():
    planned = {QN[c] for c in ("Paper", "Compound", "Condition", "Result", "Measurement", "Observation", "Evidence")}
    assert qn_terms(schema(), OWL.Class) == planned, qn_terms(schema(), OWL.Class) ^ planned


def test_every_term_has_ko_en_label_and_comment():
    g = schema()
    terms = set().union(*(qn_terms(g, k) for k in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, SKOS.Concept)))
    assert len(terms) > 100, len(terms)
    for t in terms:
        for p in (SKOS.prefLabel, SKOS.definition) if (t, RDF.type, SKOS.Concept) in g else (RDFS.label, RDFS.comment):
            assert {"ko", "en"} <= {o.language for o in g.objects(t, p)}, (t, p)


def test_domains_and_ranges_resolve():
    g = schema()
    known = qn_terms(g, OWL.Class) | {SKOS.Concept, URIRef("https://schema.org/ScholarlyArticle")}
    for p in qn_terms(g, OWL.ObjectProperty) | qn_terms(g, OWL.DatatypeProperty):
        assert set(g.objects(p, RDFS.domain)) and set(g.objects(p, RDFS.domain)) <= known, p
    for p in qn_terms(g, OWL.ObjectProperty):
        assert set(g.objects(p, RDFS.range)) and set(g.objects(p, RDFS.range)) <= known, p
    for p in qn_terms(g, OWL.DatatypeProperty):
        assert all(str(r).startswith("http://www.w3.org/2001/XMLSchema#") for r in g.objects(p, RDFS.range)), p


def test_every_concept_sits_in_a_declared_scheme():
    g = schema()
    schemes = set(g.subjects(RDF.type, SKOS.ConceptScheme))
    for c in qn_terms(g, SKOS.Concept):
        assert set(g.objects(c, SKOS.inScheme)) and set(g.objects(c, SKOS.inScheme)) <= schemes, c
    for s in schemes:
        assert list(g.subjects(SKOS.inScheme, s)), f"empty scheme {s}"


def test_competency_questions_are_exactly_the_must_have_ones():
    assert {f.stem for f in (ONTO / "cq").glob("cq*.rq")} == MUST_HAVE


def test_examples_conform_and_every_question_has_rows():
    r = check(EXAMPLES)
    assert r["conforms"] and r["n_violations"] == 0, r["violations"]
    assert not r["inconsistent"], r["inconsistent"]
    assert all(r["cq_rows"][c] > 0 for c in MUST_HAVE), r["cq_rows"]


def test_examples_are_marked_as_examples():
    for f in EXAMPLES:
        g = Graph().parse(f)
        assert {str(o) for o in g.objects(None, QN.reviewStatus)} == {"example"}, f


def test_cq22_threshold_changes_the_answer():
    g = Graph()
    for f in [*schema_files(ONTO), *EXAMPLES]:
        g.parse(f)
    low = cq(g, "cq22", {"minLogK": 3.0})
    high = cq(g, "cq22", {"minLogK": 9.0})
    assert len(low) > len(high) == 0, (len(low), len(high))


BAD = """
@prefix qn: <https://w3id.org/quinone#> .
@prefix e:  <https://w3id.org/quinone/entity/> .
@prefix schema: <https://schema.org/> .
e:bad-unit a qn:Measurement ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ;
    qn:property qn:HalfWavePotential ; qn:value -1.0 ; qn:unit qn:KJPerMol ; qn:redoxCouple qn:FirstReduction ; qn:basis qn:Experiment ; qn:method qn:CyclicVoltammetry .
e:bad-couple a qn:Measurement ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ;
    qn:property qn:HalfWavePotential ; qn:value -1.0 ; qn:unit qn:Volt ; qn:basis qn:Experiment ; qn:method qn:CyclicVoltammetry .
e:bad-method a qn:Measurement ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ;
    qn:property qn:BindingEnergy ; qn:value -50.0 ; qn:unit qn:KJPerMol ; qn:basis qn:Experiment ; qn:method qn:DFT .
e:bad-outcome a qn:Observation ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ;
    qn:observationKind qn:BindingMode ; qn:outcome qn:OxygenStable .
e:bad-page-missing a qn:Evidence ; qn:quote "a full text quote without any page number given" ; qn:evidenceSource qn:FullText .
e:bad-page-abstract a qn:Evidence ; qn:quote "an abstract quote that wrongly carries a page" ; qn:evidenceSource qn:Abstract ; qn:page 3 .
e:bad-no-evidence a qn:Observation ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:reviewStatus "example" ;
    qn:observationKind qn:OxygenStability ; qn:outcome qn:OxygenStable .
e:bad-no-solvent a qn:Condition ; qn:referenceElectrode qn:SHE ; qn:atmosphere qn:Inert .
e:bad-no-sub a qn:Compound ; schema:name "no substituent class" ; qn:skeleton qn:Anthraquinone ; qn:form qn:Molecular .
e:bad-wrong-scheme a qn:Compound ; schema:name "solvent used as skeleton" ; qn:skeleton qn:Water ; qn:form qn:Molecular ; qn:substituentClass qn:Alkyl .
e:bad-experiment-signature a qn:Measurement ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ; qn:property qn:BindingEnergy ; qn:value -50.0 ; qn:unit qn:KJPerMol ; qn:basis qn:Experiment ; qn:method qn:CyclicVoltammetry ; qn:functional "B3LYP" .
e:bad-experiment-code a qn:Measurement ; qn:ofCompound e:cpd-bq ; qn:underCondition e:cond-syn-dmf ; qn:fromPaper e:paper-syn-1 ; qn:hasEvidence e:ev-syn-2 ; qn:reviewStatus "example" ; qn:property qn:BindingEnergy ; qn:value -50.0 ; qn:unit qn:KJPerMol ; qn:basis qn:Experiment ; qn:method qn:CyclicVoltammetry ; qn:code "Gaussian" .
"""
EXPECTED = {
    "bad-unit": "unit is not allowed", "bad-couple": "needs its redox couple", "bad-method": "method does not fit",
    "bad-outcome": "does not belong to this observation kind", "bad-page-missing": "needs its page",
    "bad-page-abstract": "must not carry a page", "bad-no-evidence": "needs at least one quote",
    "bad-no-solvent": "exactly one solvent", "bad-no-sub": "substituent class", "bad-wrong-scheme": "exactly one skeleton", "bad-experiment-signature": "signatures are allowed only", "bad-experiment-code": "signatures are allowed only",
}


def test_every_rule_catches_its_bad_case():
    r = check(EXAMPLES, BAD)
    assert not r["conforms"]
    for name, text in EXPECTED.items():
        assert any(name in v and text in v for v in r["violations"]), (name, text, r["violations"])
    assert r["n_violations"] <= len(EXPECTED) + 2, r["n_violations"]  # nothing beyond the planted cases (+2 for the double-hit ones)


def test_computation_signature_contract_keeps_computation_without_reported_signatures():
    r = check(EXAMPLES)
    assert r["conforms"], r["violations"]  # omitted fields mean NotReported and remain allowed


def test_abstract_quotes_are_verbatim():
    assert DATA.is_file(), DATA
    papers = {p["doi"]: p for p in json.loads(DATA.read_text(encoding="utf-8")) if p.get("doi")}
    g = Graph()
    for f in EXAMPLES:
        g.parse(f)
    checked = 0
    for res in g.subjects(QN.fromPaper, None):
        doi = str(g.value(g.value(res, QN.fromPaper), URIRef("https://schema.org/identifier")))
        if doi not in papers:
            continue
        for ev in g.objects(res, QN.hasEvidence):
            if g.value(ev, QN.evidenceSource) == QN.Abstract:
                assert str(g.value(ev, QN.quote)) in papers[doi]["abstract"], (res, ev)
                checked += 1
    assert checked >= 5, checked


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:  # noqa: BLE001 - report every failure, then exit non-zero
                failed += 1
                print("FAIL", name, repr(e)[:600])
    sys.exit(1 if failed else 0)
