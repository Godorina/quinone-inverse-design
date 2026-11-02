"""Collapse pair_review.csv (88 pair rows) into one review row per (paper, compound).

The human checks ~22 rows instead of 88: the E2 candidate (second reduction, the couple that makes
the CO2-binding dianion), the binding value, and the CO2 standard state, each against the cited page.
"""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAIRS, SMILES, OUT = HERE / "pair_review.csv", HERE / "smiles_proposals.csv", HERE / "compound_review.csv"
COLS = ["paper_id", "compound", "name", "skeleton", "smiles", "ref_electrode",
        "E2_V", "E2_quote", "E2_page", "E2_note",
        "binding_property", "binding_value", "binding_unit", "basis", "binding_quote", "binding_page",
        "flags", "co2_standard_state", "E2_ok", "binding_ok", "verdict", "reviewer_note"]


def pick(values):
    """One distinct value -> it; several -> empty, the reviewer picks from the note."""
    return values[0] if len(values) == 1 else ""


def collapse(pairs, smiles):
    groups = defaultdict(list)
    for p in pairs:
        groups[(p["paper_id"], p["compound"])].append(p)
    out = []
    for (paper, comp), rows in sorted(groups.items()):
        # second reduction makes the dianion that binds CO2; fall back to whatever was extracted
        e2 = [r for r in rows if r["redox_couple"] == "SecondReduction"] or rows
        pots = list(dict.fromkeys((r["potential_value"], r["potential_quote"], r["potential_page"]) for r in e2))
        binds = list(dict.fromkeys((r["binding_property"], r["binding_value"], r["binding_unit"], r["basis"],
                                    r["binding_quote"], r["binding_page"]) for r in rows))
        p, b = pick(pots), pick(binds)
        s = smiles.get((paper, comp), {})
        note = []
        if e2 is rows and rows[0]["redox_couple"] != "SecondReduction":
            note.append(f"no SecondReduction extracted; couple={rows[0]['redox_couple']}")
        if len(pots) > 1:
            note.append("choose E2: " + " | ".join(f"{v} V (p.{pg}): {q[:80]}" for v, q, pg in pots))
        if len(binds) > 1:
            note.append("choose binding: " + " | ".join(f"{bp}={v} {u} {ba} (p.{pg})" for bp, v, u, ba, _, pg in binds))
        out.append({
            "paper_id": paper, "compound": comp, "name": s.get("name", ""), "skeleton": s.get("skeleton", ""),
            "smiles": s.get("canonical_smiles", ""), "ref_electrode": ";".join(sorted({r["ref_electrode"] for r in rows})),
            "E2_V": p[0] if p else "", "E2_quote": p[1] if p else "", "E2_page": p[2] if p else "", "E2_note": " ; ".join(note),
            "binding_property": b[0] if b else "", "binding_value": b[1] if b else "", "binding_unit": b[2] if b else "",
            "basis": b[3] if b else "", "binding_quote": b[4] if b else "", "binding_page": b[5] if b else "",
            "flags": ";".join(sorted({f for r in rows for f in r["flags"].split(";") if f and f != "diff_condition_key"})),
            "co2_standard_state": "", "E2_ok": "", "binding_ok": "", "verdict": "", "reviewer_note": "",
        })
    return out


def main():
    pairs = list(csv.DictReader(PAIRS.open()))
    smiles = {(r["paper_id"], r["compound"]): r for r in csv.DictReader(SMILES.open())}
    if OUT.exists() and any(r["verdict"] for r in csv.DictReader(OUT.open())):
        raise SystemExit(f"{OUT.name} already has reviewer verdicts; move it away before regenerating")
    rows = collapse(pairs, smiles)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} compounds -> {OUT.name}")


if __name__ == "__main__":
    main()
