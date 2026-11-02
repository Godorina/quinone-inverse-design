"""Phase 5 build tests. Run (from phase_5_build): ../../.venv/bin/python tests/test_build.py"""
import sys
from pathlib import Path

from rdflib import RDF, Graph, Literal, Namespace

HERE = Path(__file__).resolve().parents[1]
ONTO = HERE.parent / "phase_2_schema"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "al_alloy" / "common"))
from build import build  # noqa: E402
from check import tools  # noqa: E402

QN = Namespace("https://w3id.org/quinone#")
check, cq = tools(ONTO)
_TTL = build()
KG = HERE / "kg.ttl"
KG.write_text(_TTL, encoding="utf-8")


def test_build_is_byte_identical():
    assert build() == _TTL


def test_reparse_keeps_triple_count():
    g = Graph().parse(data=_TTL, format="turtle")
    g2 = Graph().parse(data=g.serialize(format="turtle"), format="turtle")
    assert len(g) == len(g2) > 1000


def test_every_record_measurement_has_review_status():
    g = Graph().parse(KG)
    ms = set(g.subjects(RDF.type, QN.Measurement))
    assert len(ms) > 300 and all(len(list(g.objects(m, QN.reviewStatus))) == 1 for m in ms)


def test_zero_shacl_violations_and_no_inconsistency():
    r = check([KG])
    assert r["n_violations"] == 0, r["violations"]
    assert not r["inconsistent"], r["inconsistent"]
    assert all(n > 0 for n in r["cq_rows"].values()), r["cq_rows"]


def test_computation_signature_on_experiment_is_rejected():
    g = Graph().parse(KG)
    m = next(m for m in g.subjects(QN.basis, QN.Experiment))
    bad = f'<{m}> <{QN.functional}> "B3LYP" .'
    r = check([KG], extra=bad)
    assert r["n_violations"] == 1 and "computational method signatures" in r["violations"][0], r["violations"]


def test_compound_with_smiles_carries_inchikey():
    g = Graph().parse(KG)
    cs = list(g.subjects(QN.smiles, None))
    assert cs
    for c in cs:
        assert len(list(g.objects(c, QN.inchikey))) == 1
        assert Literal("llm_checked") in set(g.objects(c, QN.smilesSource))


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
