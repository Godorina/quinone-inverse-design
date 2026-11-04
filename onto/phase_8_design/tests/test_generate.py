"""No-network contracts for the phase-8 proposal generator."""

import csv
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate import baseline, check, context, main, select


BQ = "O=C1C=CC(=O)C=C1"
F_BQ = "O=C1C=C(F)C(=O)C=C1"
CL_BQ = "O=C1C=C(Cl)C(=O)C=C1"


def tiny_context():
    return {
        "dft": [
            {"id": "D01", "smiles": BQ, "inchikey": "AZQWKYJCGOJGHM-UHFFFAOYSA-N"},
            {"id": "D02", "smiles": F_BQ, "inchikey": "ACDQKMGNQHDBNL-UHFFFAOYSA-N"},
        ],
        "kg": [{"id": "K001", "iri": "urn:k:1", "name": "evidence"}],
        "domain": "v1", "kg_inchikeys": set(), "cores_smarts": [BQ], "allowed_subst": {"F", "Cl"},
        "ref_fps": [BQ, F_BQ], "line": {"a": -1, "b": 0, "sigma": 1},
    }


def proposal(**overrides):
    value = {"parent_id": "D01", "smiles": CL_BQ, "edits": ["add Cl"],
             "cited_ids": ["K001"], "hypothesis": "test"}
    value.update(overrides)
    return value


def test_check_rejects_bad_citation_parent_structure_and_duplicates():
    ctx = tiny_context()
    assert check(proposal(cited_ids=["K999"]), ctx, set()) == "bad_citation"
    assert check(proposal(parent_id="D99"), ctx, set()) == "bad_parent"
    assert check(proposal(smiles="c1ccccc1"), ctx, set()) == "not_quinone"
    assert check(proposal(smiles="O=C1C=C(I)C(=O)C=C1"), ctx, set()) == "unregistered_substituent"
    assert check(proposal(smiles=BQ), ctx, set()) == "duplicate"
    assert check(proposal(), ctx, {"WOGWYSWDBYCVDY-UHFFFAOYSA-N"}) == "duplicate"


def test_select_keeps_order_and_one_substituent_set_per_core():
    selected = select([proposal(smiles=CL_BQ), proposal(smiles="O=C1C(Cl)=CC(=O)C=C1"),
                       proposal(smiles=F_BQ)], n=10)
    assert [row["smiles"] for row in selected] == [CL_BQ, F_BQ]


def test_baseline_matches_parent_mix_and_all_rows_pass_check():
    ctx = tiny_context()
    parents = ["D01", "D02", "D01", "D02"]
    rows = baseline(ctx, parents, n=4, seed=8)
    assert len(rows) == 4
    assert Counter(row["parent_id"] for row in rows) == Counter(parents)
    seen = set()
    for row in rows:
        assert check(row, ctx, seen) is None
        seen.add(row["inchikey"])


def test_context_reads_fifteen_dft_rows_and_kg_evidence():
    ctx = context()
    assert len(ctx["dft"]) == 15
    assert all("f" in row for row in ctx["dft"])
    assert len(ctx["kg"]) >= 1


def test_replay_reproduces_selected_output(tmp_path):
    replay = tmp_path / "responses.jsonl"
    replay.write_text(json.dumps({"structured_output": {"proposals": [proposal()]}}) + "\n")
    out = tmp_path / "run"
    main(["--calls", "1", "--replay", str(replay), "--out", str(out)])
    rows = list(csv.DictReader((out / "selected_llm.csv").open()))
    assert len(rows) == 1 and rows[0]["smiles"] == CL_BQ
    assert (out / "responses.jsonl").read_text() == replay.read_text()


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    with tempfile.TemporaryDirectory() as directory:
        for test in tests:
            if "tmp_path" in test.__code__.co_varnames:
                path = Path(directory) / test.__name__
                path.mkdir()
                test(path)
            else:
                test()
    print(f"{len(tests)} passed")
