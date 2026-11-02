from collections.abc import Sequence
from pathlib import Path

import pytest

from qextract.llm import LlmUnavailableError, Message
from qextract.pipeline import PaperInput, extract, render
from qextract.prompt import build_system
from qextract.record import CompoundRec
from qextract.text import split_pages
from qextract.vocab import Vocabulary, load

VOCAB_TTL = Path(__file__).parent / "fixtures" / "quinone-vocab.ttl"
TEXT = """
===== PAGE 1 =====
Title page. 9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile versus Ag/AgCl.
===== PAGE 2 =====
The half-wave potential E1/2 shifted to -0.85 V vs Ag/AgCl at 0.66 M ethanol.
"""
COMPOUND = (
    '{"key":"paq","name":"9,10-Phenanthrenequinone","skeleton":"Phenanthrenequinone","form":"Molecular",'
    '"substituent_classes":["Unsubstituted"],"quote":"9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile"}'
)
CONDITION = (
    '{"key":"c1","solvent":"Acetonitrile","reference_electrode":"AgAgCl","atmosphere":"NotReported",'
    '"quote":"PAQ) was studied in acetonitrile versus Ag/AgCl"}'
)


def measurement(quote: str) -> str:
    return (
        '{"compound":"paq","condition":"c1","property":"HalfWavePotential","value":-0.85,"unit":"Volt",'
        f'"basis":"Experiment","method":"NotReported","redox_couple":"SecondReduction","quote":"{quote}"}}'
    )


def record(*measurements: str) -> str:
    return f'{{"compounds":[{COMPOUND}],"conditions":[{CONDITION}],"measurements":[{",".join(measurements)}]}}'


GOOD = measurement("The half-wave potential E1/2 shifted to -0.85 V vs Ag/AgCl at 0.66 M ethanol")
BAD = measurement("the half wave potential moved to minus 0.85 volts")
PAPER = PaperInput("m999", "Test paper", split_pages(TEXT), abstract_only=False)


class Scripted:
    replies: list[str]
    seen: list[Sequence[Message]]

    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self.seen = []

    def __call__(self, messages: Sequence[Message]) -> str:
        self.seen.append(list(messages))
        return self.replies[len(self.seen) - 1]


@pytest.fixture(scope="module")
def vocab() -> Vocabulary:
    return load(VOCAB_TTL)


def test_refusals_go_back_to_the_model_and_the_fixed_item_is_saved(vocab: Vocabulary) -> None:
    model = Scripted([record(BAD), record(GOOD)])
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=3)
    assert len(outcome.checked.measurements) == 1
    assert [a.dropped for a in outcome.attempts] == [1, 0]
    assert "not verbatim" in model.seen[1][-1].content
    assert model.seen[1][-2].role == "assistant"


def test_invalid_json_is_repaired_not_crashed(vocab: Vocabulary) -> None:
    model = Scripted(["not json at all", record(GOOD)])
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=3)
    assert len(outcome.checked.measurements) == 1
    assert outcome.attempts[0].parse_errors


def test_best_attempt_is_kept_when_the_model_never_gets_it_right(vocab: Vocabulary) -> None:
    model = Scripted([record(GOOD, BAD), record(BAD), record(BAD)])
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=2)
    assert len(outcome.checked.measurements) == 1
    assert len(outcome.checked.dropped) == 1


def test_retries_are_bounded(vocab: Vocabulary) -> None:
    model = Scripted([record(BAD)] * 10)
    extract(PAPER, vocab, build_system(vocab), model, retries=1)
    assert len(model.seen) == 2


def test_unreachable_model_is_not_swallowed(vocab: Vocabulary) -> None:
    def down(_: Sequence[Message]) -> str:
        raise LlmUnavailableError(url="http://x", reason="refused")

    with pytest.raises(LlmUnavailableError):
        extract(PAPER, vocab, build_system(vocab), down)


def test_saved_json_lists_pages_and_reasons(vocab: Vocabulary) -> None:
    outcome = extract(PAPER, vocab, build_system(vocab), Scripted([record(GOOD, BAD)] * 4), retries=0)
    saved = render(PAPER, outcome)
    assert '"page": 2' in saved
    assert "not verbatim" in saved
    assert '"review_status": "machine_extracted"' in saved


def test_one_malformed_item_drops_only_that_item(vocab: Vocabulary) -> None:
    too_long = measurement("x" * 800)
    model = Scripted([record(GOOD, too_long)] * 4)
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=0)
    assert len(outcome.checked.measurements) == 1
    assert len(outcome.checked.compounds) == 1
    assert len(outcome.checked.dropped) == 1
    assert "700" in render(PAPER, outcome)


def test_item_with_a_missing_field_is_dropped_not_fatal(vocab: Vocabulary) -> None:
    broken = '{"compound":"paq","condition":"c1","value":-0.85}'
    model = Scripted([record(GOOD, broken)] * 4)
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=0)
    assert len(outcome.checked.measurements) == 1
    assert [d.kind for d in outcome.checked.dropped] == ["measurement"]


def test_non_object_reply_is_still_a_parse_failure(vocab: Vocabulary) -> None:
    model = Scripted(["[1, 2, 3]"] * 4)
    outcome = extract(PAPER, vocab, build_system(vocab), model, retries=0)
    assert outcome.attempts[0].parse_errors
    assert not outcome.checked.measurements


TABLE_TEXT = """
===== PAGE 1 =====
Table 1. Potentials of quinones in MeCN vs Fc/Fc+
DDQ 0.12 0.45
TCNQ -0.20 0.31
DDQ 0.12 0.99
"""


def table_paper() -> PaperInput:
    return PaperInput("m998", "Table paper", split_pages(TABLE_TEXT), abstract_only=False)


def table_reply(row_quote: str, value: float) -> str:
    compound = (
        '{"key":"tcnq","name":"TCNQ","skeleton":"OtherQuinoid","form":"Molecular","substituent_classes":["Unsubstituted"],'
        '"quote":"Table 1. Potentials of quinones in MeCN vs Fc/Fc+"}'
    )
    cond = (
        '{"key":"c1","solvent":"Acetonitrile","reference_electrode":"FcFcPlus","atmosphere":"NotReported",'
        '"quote":"Table 1. Potentials of quinones in MeCN vs Fc/Fc+"}'
    )
    m = (
        '{"compound":"tcnq","condition":"c1","property":"ReductionPotential","value":' + str(value) + ',"unit":"Volt",'
        '"basis":"Experiment","method":"CyclicVoltammetry","redox_couple":"FirstReduction","quote":"' + row_quote + '"}'
    )
    return f'{{"compounds":[{compound}],"conditions":[{cond}],"measurements":[{m}]}}'


def test_a_short_table_row_is_a_valid_quote_when_it_is_unique(vocab: Vocabulary) -> None:
    outcome = extract(
        table_paper(), vocab, build_system(vocab), Scripted([table_reply("TCNQ -0.20 0.31", -0.2)]), retries=0
    )
    assert not outcome.checked.dropped
    assert len(outcome.checked.measurements) == 1


def test_a_short_quote_that_appears_twice_is_refused(vocab: Vocabulary) -> None:
    outcome = extract(table_paper(), vocab, build_system(vocab), Scripted([table_reply("DDQ 0.12", 0.12)]), retries=0)
    assert not outcome.checked.measurements
    assert "more than once" in render(table_paper(), outcome)


def test_compound_key_may_be_long() -> None:
    rec = CompoundRec.model_validate(
        {
            "key": "dichloronaphthoquinone",
            "name": "1,2-dichloronaphthoquinone",
            "skeleton": "Naphthoquinone",
            "form": "Molecular",
            "substituent_classes": ["ElectronWithdrawing"],
            "quote": "1,2-dichloronaphthoquinone",
        }
    )
    assert rec.key == "dichloronaphthoquinone"
