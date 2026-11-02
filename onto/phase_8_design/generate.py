"""Generate and ledger KG-grounded phase-8 quinone proposals."""

import argparse
import csv
import hashlib
import json
import random
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from rdkit import Chem

from loop import QUINONES, edit, in_domain, t0


ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "phase_5_build" / "kg.ttl"
SUMMARY = ROOT.parents[0] / "dft" / "runs" / "ref_set" / "summary.json"
SMILES = ROOT / "phase_4b_extend" / "smiles_proposals.csv"
QN = Namespace("https://w3id.org/quinone#")
CORE_SMARTS = ("O=C1C=CC(=O)C=C1", "O=C1C(=O)c2ccccc2C=C1", "O=C1C=CC2=CC=CC=C2C1=O",
               "O=C1C=CC(=O)c2ccccc21", "O=C1c2ccccc2C(=O)c2ccccc21", "O=C1C(=O)c2ccccc2-c2ccccc21")


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _inchikey(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToInchiKey(mol) if mol else None


def _substituents(smiles, cores=CORE_SMARTS):
    """Return the matched core index and directly attached substituent atom symbols."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, ()
    for index, value in enumerate(cores):
        core = Chem.MolFromSmarts(value)
        if core and mol.HasSubstructMatch(core):
            atoms = set(mol.GetSubstructMatch(core))
            return index, tuple(sorted(atom.GetSymbol() for atom in mol.GetAtoms()
                                       if atom.GetIdx() not in atoms and
                                       any(n.GetIdx() in atoms for n in atom.GetNeighbors())))
    return None, ()


def context(kg_path=KG, summary_path=SUMMARY, smiles_path=SMILES):
    """Load compact DFT/KG evidence tables, preserving their source identifiers."""
    summary = json.loads(Path(summary_path).read_text())
    records, allowed = {}, set()
    with open(smiles_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["canonical_smiles"] and row["inchikey"]:
                records.setdefault(row["inchikey"], row)
                mol = Chem.MolFromSmiles(row["canonical_smiles"])
                if mol:
                    for atom in mol.GetAtoms():
                        if not atom.IsInRing() and any(neighbor.IsInRing() for neighbor in atom.GetNeighbors()):
                            allowed.add(atom.GetSymbol())
    line, dft = summary["line"], []
    for index, value in enumerate(summary["molecules"], 1):
        source = records.get(value["inchikey"])
        if not source:
            continue
        f = (line["a"] * value["E2_eV"] + line["b"] - value["dE_bind_kcal"]) / line["sigma"]
        dft.append({"id": f"D{index:02d}", "smiles": source["canonical_smiles"], "inchikey": value["inchikey"],
                    "name": source["name"], "E2_eV": value["E2_eV"], "dE_bind_kcal": value["dE_bind_kcal"],
                    "co2_detached": value["co2_detached"], "o2_margin_V": value["E_O2_eV"] - value["E2_eV"], "f": f})
    graph, schema = Graph().parse(kg_path, format="turtle"), Namespace("https://schema.org/")
    kg, kg_inchikeys = [], set()
    for compound in sorted(graph.subjects(RDF.type, QN.Compound), key=str):
        name, smiles, key = graph.value(compound, schema.name), graph.value(compound, QN.smiles), graph.value(compound, QN.inchikey)
        if key:
            kg_inchikeys.add(str(key))
        measurements = []
        for m in graph.subjects(QN.ofCompound, compound):
            if (m, RDF.type, QN.Measurement) not in graph:
                continue
            condition = graph.value(m, QN.underCondition)
            measurements.append({"property": str(graph.value(m, QN.property) or "").rsplit("#", 1)[-1], "value": str(graph.value(m, QN.value) or ""), "unit": str(graph.value(m, QN.unit) or "").rsplit("#", 1)[-1], "solvent": str(graph.value(condition, QN.solvent) or "").rsplit("#", 1)[-1], "reference_electrode": str(graph.value(condition, QN.referenceElectrode) or "").rsplit("#", 1)[-1], "review_status": str(graph.value(m, QN.reviewStatus) or "")})
        observations = [str(graph.value(o, QN.outcome) or "").rsplit("#", 1)[-1] for o in graph.subjects(QN.ofCompound, compound) if (o, RDF.type, QN.Observation) in graph]
        if measurements or observations:
            kg.append({"id": f"K{len(kg)+1:03d}", "iri": str(compound), "name": str(name or ""), "smiles": str(smiles or ""), "inchikey": str(key or ""), "measurements": measurements, "oxygen_observations": observations})
    # experimental molecules entered from papers (e.g. Alherz 2022 Table 1) are known, not new, even if not yet in the KG
    with open(ROOT / "phase_4b_extend/alherz2022_table1.csv", newline="") as handle:
        kg_inchikeys |= {r["inchikey"] for r in csv.DictReader(handle) if r.get("inchikey")}
    return {"dft": dft, "kg": kg, "kg_inchikeys": kg_inchikeys, "cores_smarts": list(CORE_SMARTS), "allowed_subst": allowed & {"F", "Cl", "Br", "N", "O"}, "ref_fps": [row["smiles"] for row in dft], "line": line}


def prompt(ctx, previous_smiles):
    dft = "\n".join(f"{r['id']} {r['smiles']} E2={r['E2_eV']:.3f} eV bind={r['dE_bind_kcal']:.2f} f={r['f']:.2f} O2margin={r['o2_margin_V']:.3f} detached={r['co2_detached']}" for r in ctx["dft"])
    kg = "\n".join(f"{r['id']} {r['name']} {r['smiles']} {r['measurements']} O2={r['oxygen_observations']}" for r in ctx["kg"])
    return f"""Propose exactly 10 quinone CO2-capture candidates, or return insufficient_evidence.
Goal: f >= 2 relative to the exchange line, O2 margin >= 0.15 V, and no CO2 detachment.
Use a D parent and KG citations only. Edit only by add/replace/remove/move of F, Cl, Br, NH2, OH; use BQ/NQ/AQ/PQ cores.
Do not repeat these SMILES: {json.dumps(sorted(previous_smiles))}
Return JSON {{\"proposals\":[{{\"parent_id\":\"D01\",\"smiles\":\"...\",\"edits\":[\"...\"],\"cited_ids\":[\"K001\"],\"hypothesis\":\"...\"}}]}}.
DFT evidence:\n{dft}\nKG evidence:\n{kg}"""


def call_llm(text):
    schema = {"type": "object", "properties": {"proposals": {"type": "array"}, "reason": {"type": "string"}}, "required": ["proposals"]}
    result = subprocess.run([str(Path.home() / ".local/bin/claude"), "-p", "--model", "sonnet", "--tools", "", "--output-format", "json", "--json-schema", json.dumps(schema), "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config"], input=text, text=True, capture_output=True, timeout=900, check=True)
    return json.loads(result.stdout)


def check(proposal, ctx, seen):
    smiles = proposal.get("smiles") if isinstance(proposal, dict) else None
    if not isinstance(smiles, str):
        return "invalid_smiles"
    reason = t0(smiles) or in_domain(smiles, ctx["cores_smarts"], ctx["allowed_subst"], ctx["ref_fps"])
    if reason:
        return reason
    if not set(proposal.get("cited_ids", [])) <= {row["id"] for row in ctx["kg"] + ctx["dft"]}:  # D (our DFT) and K (literature) are both evidence
        return "bad_citation"
    if proposal.get("parent_id") not in {row["id"] for row in ctx["dft"]}:
        return "bad_parent"
    key = _inchikey(smiles)
    if key in {row["inchikey"] for row in ctx["dft"]} or key in ctx["kg_inchikeys"] or key in seen:
        return "duplicate"
    return None


def select(checked, n=10):
    chosen, families = [], set()
    for row in checked:
        family = _substituents(row["smiles"])
        if family not in families:
            chosen.append(row)
            families.add(family)
        if len(chosen) == n:
            break
    return chosen


def baseline(ctx, parents_used, n=10, seed=0):
    rng, targets, rows, seen, attempts = random.Random(seed), Counter(parents_used), [], set(), 0
    parents = {row["id"]: row for row in ctx["dft"]}
    for parent_id, count in targets.items():
        for _ in range(count):
            while attempts < 2000:
                attempts += 1
                smiles = edit(parents[parent_id]["smiles"], rng.choice(["add", "replace", "remove", "move"]), substituents=sorted(ctx["allowed_subst"]), rng=rng)
                row = {"parent_id": parent_id, "smiles": smiles, "edits": ["random_edit"], "cited_ids": [], "hypothesis": "B0 random edit", "arm": "b0"}
                if smiles and check(row, ctx, seen) is None:
                    row["inchikey"] = _inchikey(smiles)
                    seen.add(row["inchikey"])
                    rows.append(row)
                    break
            else:
                raise RuntimeError(f"baseline exhausted for {parent_id}")
    return rows[:n]


def _write_csv(path, rows):
    fields = ["id", "smiles", "inchikey", "parent_id", "cited_ids", "hypothesis", "arm"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for index, row in enumerate(rows, 1):
            writer.writerow({**row, "id": f"{row.get('arm', 'llm').upper()}{index:02d}", "cited_ids": ";".join(row.get("cited_ids", []))})


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--calls", type=int, default=4)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    ctx, seen, checked, responses = context(), set(), [], []
    out = args.out or Path(__file__).with_name("runs") / datetime.now().strftime("%Y%m%d-%H%M")
    out.mkdir(parents=True, exist_ok=True)
    replay = args.replay.read_text().splitlines() if args.replay else []
    for index in range(args.calls):
        text = prompt(ctx, [row["smiles"] for row in checked])  # SMILES, not InChIKeys: the LLM can only avoid what it can read
        (out / f"prompt_{index + 1}.txt").write_text(text, encoding="utf-8")
        if args.dry_run:
            break
        response = json.loads(replay[index]) if args.replay else call_llm(text)
        responses.append(response)
        for proposal in response.get("structured_output", response).get("proposals", []):
            reason, key = check(proposal, ctx, seen), _inchikey(proposal.get("smiles", ""))
            row = {**proposal, "inchikey": key, "reason": reason}
            if reason is None:
                seen.add(key)
                checked.append(row)
            with open(out / "ledger.jsonl", "a", encoding="utf-8") as ledger:
                ledger.write(json.dumps(row, sort_keys=True) + "\n")
    if args.replay:
        shutil.copyfile(args.replay, out / "responses.jsonl")
    elif responses:
        (out / "responses.jsonl").write_text("".join(json.dumps(row) + "\n" for row in responses), encoding="utf-8")
    selected = select(checked)
    for row in selected:
        row["arm"] = "llm"
    _write_csv(out / "selected_llm.csv", selected)
    _write_csv(out / "selected_b0.csv", baseline(ctx, [row["parent_id"] for row in selected]) if selected else [])
    manifest = {"kg_sha256": _hash(KG), "summary_sha256": _hash(SUMMARY), "calls": args.calls, "total_cost_usd": sum(row.get("total_cost_usd", 0) for row in responses)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    main()
