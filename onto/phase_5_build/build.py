"""Phase 5: records_final/*.json (+ 4b tables) -> kg.ttl. Run: ../../.venv/bin/python build.py"""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

ONTO = Path(__file__).resolve().parents[1]
QN = Namespace("https://w3id.org/quinone#")
E = Namespace("https://w3id.org/quinone/entity/")
S = Namespace("https://schema.org/")


def _iri(*parts) -> URIRef:
    return E["-".join(quote(str(p), safe="") for p in parts)]


def build(skipped: list | None = None) -> str:
    skipped = [] if skipped is None else skipped  # filled with (paper, node id, quote) of results left out
    g = Graph()
    g.bind("qn", QN), g.bind("e", E), g.bind("schema", S)
    master = {m["id"]: m for m in json.loads((ONTO / "phase_3_corpus/master.json").read_text(encoding="utf-8"))}
    tier = {r["doi"]: r["xlsx_tier"] for r in csv.DictReader(open(ONTO / "phase_4b_extend/xlsx_status.csv", encoding="utf-8"))}
    smiles = {(r["paper_id"], r["compound"]): r for r in
              csv.DictReader(open(ONTO / "phase_4b_extend/smiles_proposals.csv", encoding="utf-8")) if r["canonical_smiles"]}

    def evidence(pid, source, quote_, page):
        ev = _iri("ev", pid, hashlib.sha1(f"{quote_}|{page}".encode()).hexdigest()[:10])
        g.add((ev, RDF.type, QN.Evidence))
        g.add((ev, QN.evidenceSource, QN[source]))
        g.add((ev, QN.quote, Literal(quote_)))
        if page:
            g.add((ev, QN.page, Literal(page, datatype=XSD.integer)))
        return ev

    for f in sorted((ONTO / "phase_4_extract/records_final").glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        pid, src = rec["paper_id"], rec["evidence_source"]
        paper = _iri("paper", pid)
        g.add((paper, RDF.type, QN.Paper))
        g.add((paper, S.name, Literal(rec["title"])))
        g.add((paper, S.identifier, Literal(master[pid]["doi"])))
        g.add((paper, S.datePublished, Literal(str(master[pid]["year"]))))
        if master[pid]["doi"] in tier:
            g.add((paper, QN.simReviewTier, Literal(tier[master[pid]["doi"]])))

        for c in rec["compounds"]:
            cpd = _iri("cpd", pid, c["key"])
            g.add((cpd, RDF.type, QN.Compound))
            g.add((cpd, S.name, Literal(c["name"])))
            g.add((cpd, QN.skeleton, QN[c["skeleton"]]))
            g.add((cpd, QN.form, QN[c["form"]]))
            for sc in c["substituent_classes"]:
                g.add((cpd, QN.substituentClass, QN[sc]))
            if c["substituent_text"]:
                g.add((cpd, QN.substituentText, Literal(c["substituent_text"])))
            if (pid, c["key"]) in smiles:
                p = smiles[pid, c["key"]]
                g.add((cpd, QN.smiles, Literal(p["canonical_smiles"])))
                g.add((cpd, QN.inchikey, Literal(p["inchikey"])))
                g.add((cpd, QN.smilesSource, Literal("llm_checked")))

        for c in rec["conditions"]:
            cond = _iri("cond", pid, c["key"])
            g.add((cond, RDF.type, QN.Condition))
            g.add((cond, QN.solvent, QN[c["solvent"]]))
            g.add((cond, QN.referenceElectrode, QN[c["reference_electrode"]]))
            g.add((cond, QN.atmosphere, QN[c["atmosphere"]]))
            for k, p in (("electrolyte_text", QN.electrolyteText), ("additive_text", QN.additiveText)):
                if c[k]:
                    g.add((cond, p, Literal(c[k])))
            if c["ph"] is not None:
                g.add((cond, QN.pH, Literal(str(c["ph"]), datatype=XSD.decimal)))
            if c["temperature_k"] is not None:
                g.add((cond, QN.temperatureK, Literal(str(c["temperature_k"]), datatype=XSD.decimal)))

        def result(node, cls, r):
            if len(r["quote"]) < 20:  # EvidenceShape: quote >= 20 chars; the quote is data, so the result is left out, not padded
                skipped.append((pid, node.split("/")[-1], r["quote"]))
                return False
            g.add((node, RDF.type, cls))
            g.add((node, QN.ofCompound, _iri("cpd", pid, r["compound"])))
            g.add((node, QN.underCondition, _iri("cond", pid, r["condition"])))
            g.add((node, QN.fromPaper, paper))
            g.add((node, QN.hasEvidence, evidence(pid, src, r["quote"], r["page"])))
            g.add((node, QN.reviewStatus, Literal(rec["review_status"])))
            return True

        for i, m in enumerate(rec["measurements"]):
            node = _iri("m", pid, i)
            if not result(node, QN.Measurement, m):
                continue
            g.add((node, QN.property, QN[m["property"]]))
            g.add((node, QN.value, Literal(str(m["value"]), datatype=XSD.decimal)))
            g.add((node, QN.unit, QN[m["unit"]]))
            g.add((node, QN.basis, QN[m["basis"]]))
            g.add((node, QN.method, QN[m["method"]]))
            if m["redox_couple"]:
                g.add((node, QN.redoxCouple, QN[m["redox_couple"]]))
        for i, o in enumerate(rec["observations"]):
            node = _iri("o", pid, i)
            if not result(node, QN.Observation, o):
                continue
            g.add((node, QN.observationKind, QN[o["kind"]]))
            g.add((node, QN.outcome, QN[o["outcome"]]))

    # ponytail: rdflib turtle sorts subjects/predicates/objects, so no extra canonicalization (no blank nodes are emitted)
    return g.serialize(format="turtle")


if __name__ == "__main__":
    out = Path(__file__).with_name("kg.ttl")
    skipped = []
    out.write_text(build(skipped), encoding="utf-8")
    print(f"wrote {out}; skipped {len(skipped)} results with quote < 20 chars")
