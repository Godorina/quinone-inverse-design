"""Prompt and filter must agree: what the loop prompt allows, check() accepts, and D citations count as evidence."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("generate", HERE / "generate.py")
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
CTX = gen.context()


def test_dft_reference_ids_are_valid_citations():
    p = {"parent_id": "D08", "smiles": "O=C1C(F)=C(F)C(=O)C(F)=C1Cl", "cited_ids": ["D08", "D07"], "edits": [], "hypothesis": ""}
    assert gen.check(p, CTX, set()) is None


def test_unknown_citation_still_rejected():
    p = {"parent_id": "D08", "smiles": "O=C1C(F)=C(F)C(=O)C(F)=C1Cl", "cited_ids": ["D99"], "edits": [], "hypothesis": ""}
    assert gen.check(p, CTX, set()) == "bad_citation"


def test_loop_allows_cn_in_v2():
    text = (HERE / "closed_loop.py").read_text()
    assert "at most 30 heavy atoms" in text
    p = {"parent_id": "D08", "smiles": "O=C1C(F)=C(F)C(=O)C(F)=C1C#N", "cited_ids": ["D08"], "edits": [], "hypothesis": ""}
    assert gen.check(p, CTX, set()) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
