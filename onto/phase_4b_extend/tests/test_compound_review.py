import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compound_review", ROOT / "compound_review.py")
cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)


def row(comp, couple, e, b):
    return {"paper_id": "p", "compound": comp, "redox_couple": couple, "potential_value": e, "potential_quote": f"q{e}",
            "potential_page": "1", "binding_property": "Log10BindingConstant", "binding_value": b, "binding_unit": "Dimensionless",
            "basis": "Experiment", "binding_quote": f"k{b}", "binding_page": "2", "ref_electrode": "FcFcPlus", "flags": "diff_condition_key"}


def test_one_row_per_compound_and_second_reduction_is_picked():
    pairs = [row("a", "FirstReduction", "-0.5", "5"), row("a", "SecondReduction", "-1.2", "5"),
             row("b", "SecondReduction", "-1.0", "3"), row("b", "SecondReduction", "-1.1", "3")]
    out = {r["compound"]: r for r in cr.collapse(pairs, {})}
    assert len(out) == 2
    assert out["a"]["E2_V"] == "-1.2" and out["a"]["binding_value"] == "5" and out["a"]["E2_note"] == ""
    assert out["b"]["E2_V"] == "" and "choose E2" in out["b"]["E2_note"]  # ambiguous -> human picks
    assert out["a"]["flags"] == ""  # diff_condition_key is implied by collapsing, not a review flag


def test_real_table_has_22_compounds_matching_pairs():
    import csv
    pairs = {(r["paper_id"], r["compound"]) for r in csv.DictReader((ROOT / "pair_review.csv").open())}
    rows = list(csv.DictReader((ROOT / "compound_review.csv").open()))
    assert {(r["paper_id"], r["compound"]) for r in rows} == pairs and len(rows) == len(pairs) == 22


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
