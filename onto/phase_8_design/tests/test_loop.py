"""Scriptable contract tests for the phase-8 closed-loop skeleton."""

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop import auc, edit, in_domain, objective, run, t0


BQ = "O=C1C=CC(=O)C=C1"
DOMAIN = {"cores_smarts": [BQ], "allowed_subst": {"F"}, "ref_fps": [BQ]}
FEEDBACK_DOMAIN = {**DOMAIN, "ref_fps": [BQ, "O=C1C=C(F)C(=O)C(F)=C1"]}


def test_t0_accepts_quinone_and_rejects_benzene_and_metal():
    assert t0(BQ) is None
    assert t0("c1ccccc1") == "not_quinone"
    assert t0("O=C1C=CC(=O)C=C1.[Fe]") == "metal"


def test_domain_rejects_wrong_core_and_unregistered_substituent():
    assert in_domain("c1ccccc1", [BQ], {"F"}, [BQ]) == "out_of_domain_core"
    chlorinated = edit(BQ, "add", substituents=["Cl"], position=2)
    assert in_domain(chlorinated, [BQ], {"F"}, [BQ]) == "unregistered_substituent"


def test_objective_applies_o2_margin_and_auc_is_hand_calculated():
    assert objective(0.4, -1.0, 2.0, 0.0, 2.0, 0.1) == 0.9
    assert objective(0.2, -1.0, 2.0, 0.0, 2.0, 0.1) is None
    assert auc([1.0, 1.5, 2.0], 1.0) == 1.5


def test_invalid_proposals_consume_every_budget_step_and_write_ledger(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    curve = run(lambda _: [{"smiles": ""}], lambda _: 9.0, [BQ], ledger_path=ledger, **DOMAIN)
    assert len(curve) == 80
    assert curve == [9.0] * 80
    assert len(ledger.read_text().splitlines()) == 80
    assert all(json.loads(line)["reason"] == "invalid_smiles" for line in ledger.read_text().splitlines())


def test_insufficient_evidence_consumes_remaining_budget_without_improvement(tmp_path):
    calls = []

    def propose(context):
        calls.append(context)
        return [{"reason": "insufficient_evidence"}]

    curve = run(propose, lambda _: 3.0, [BQ], budget=4, ledger_path=tmp_path / "ledger.jsonl", **DOMAIN)
    assert curve == [3.0] * 4
    assert len(calls) == 1


def test_feedback_strictly_improves_over_feedback_free_path(tmp_path):
    evaluate = lambda smiles: smiles.count("F")

    def proposer(seed):
        rng = random.Random(seed)

        def propose(context):
            parent = context["top"][0]["smiles"] if "top" in context else context["start_smiles"][0]
            return [{"smiles": edit(parent, "add", substituents=["F"], rng=rng)}]

        return propose

    with_feedback = run(proposer(11), evaluate, [BQ], budget=8,
                        ledger_path=tmp_path / "with.jsonl", **FEEDBACK_DOMAIN)
    without_feedback = run(proposer(11), evaluate, [BQ], budget=8, feedback=False,
                           ledger_path=tmp_path / "without.jsonl", **FEEDBACK_DOMAIN)
    assert with_feedback[-1] > without_feedback[-1]


def test_out_of_domain_skips_evaluation_and_consumes_budget(tmp_path):
    calls = []
    curve = run(lambda _: [{"smiles": "O=C1C=C(Cl)C(=O)C=C1"}], lambda smiles: calls.append(smiles),
                [{"smiles": BQ, "f": 2.0}], ledger_path=tmp_path / "ledger.jsonl", **DOMAIN)
    rows = [json.loads(line) for line in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert calls == []
    assert curve == [2.0] * 80
    assert all(row["reason"] == "out_of_domain" for row in rows)


def test_b2_context_has_only_scoreless_start_and_previous_smiles(tmp_path):
    contexts = []

    def propose(context):
        contexts.append(context)
        return [{"reason": "insufficient_evidence"}]

    run(propose, lambda _: 1.0, [{"smiles": BQ, "f": 4.0}], budget=2, feedback=False,
        ledger_path=tmp_path / "ledger.jsonl", **DOMAIN)
    assert contexts == [{"previous_smiles": [BQ], "start_smiles": [BQ], "round": 0}]


def test_evaluation_exception_is_recorded_and_does_not_stop_run(tmp_path):
    curve = run(lambda _: [{"smiles": "O=C1C=C(F)C(=O)C=C1"}],
                lambda _: (_ for _ in ()).throw(RuntimeError("xTB failed")),
                [{"smiles": BQ, "f": 5.0}], ledger_path=tmp_path / "ledger.jsonl", **DOMAIN)
    rows = [json.loads(line) for line in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert curve == [5.0] * 80
    assert all(row["reason"] == "calculation_fail: RuntimeError" for row in rows)


def test_start_best_uses_the_largest_starting_score(tmp_path):
    curve = run(lambda _: [{"reason": "insufficient_evidence"}], lambda _: 0.0,
                [{"smiles": BQ, "f": 1.0}, {"smiles": "O=C1C=C(F)C(=O)C=C1", "f": 3.0}], budget=2,
                ledger_path=tmp_path / "ledger.jsonl", **DOMAIN)
    assert curve == [3.0, 3.0]


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    with tempfile.TemporaryDirectory() as temp:
        for test in tests:
            if "tmp_path" in test.__code__.co_varnames:
                case_dir = Path(temp) / test.__name__
                case_dir.mkdir()
                test(case_dir)
            else:
                test()
    print(f"{len(tests)} passed")
