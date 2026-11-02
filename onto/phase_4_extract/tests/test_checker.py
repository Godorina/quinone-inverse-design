import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from qextract.checker import (
    AtmosphereContradicts,
    BoundNotValue,
    Checked,
    CitedValue,
    ComputationWithoutEvidence,
    ComputationSignatureOnExperiment,
    ConflictingValues,
    DanglingReference,
    EvidenceMissing,
    MethodBasisMismatch,
    NameNotInText,
    OtherQuantity,
    OtherSpeciesPotential,
    OutcomeKindMismatch,
    Problem,
    ProvenanceMismatch,
    QuoteNotFound,
    RangeBound,
    RedoxCoupleMissing,
    ReferenceContradicts,
    ScaleNotApplied,
    UnitNotAllowed,
    UnitNotInQuote,
    UnknownTerm,
    UnrelatedNumber,
    ValueNotInQuote,
    check,
)
from qextract.record import PaperRecord
from qextract.text import QuoteFound, QuoteMissing, before_value, contains, find_quote, numbers_in, split_pages
from qextract.vocab import Vocabulary, load

VOCAB_TTL = Path(__file__).parent / "fixtures" / "quinone-vocab.ttl"

PAPER = """
===== PAGE 1 =====
Title page. 9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile.
===== PAGE 2 =====
The half-wave potential E1/2 shifted to \u22120.85 V vs Ag/AgCl at 0.66 M ethanol, and
log(KCO2) was 8.55. Energy consumption fell from 73.43 to 50.94 kJ/mol. Super-
saturated solutions were avoided.
"""

COMPOUND = {
    "key": "paq",
    "name": "9,10-Phenanthrenequinone",
    "skeleton": "Phenanthrenequinone",
    "form": "Molecular",
    "substituent_classes": ["Unsubstituted"],
    "quote": "9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile.",
}
CONDITION = {
    "key": "c1",
    "solvent": "Acetonitrile",
    "reference_electrode": "AgAgCl",
    "atmosphere": "NotReported",
    "quote": "9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile.",
}
POTENTIAL = {
    "compound": "paq",
    "condition": "c1",
    "property": "HalfWavePotential",
    "value": -0.85,
    "unit": "Volt",
    "basis": "Experiment",
    "method": "NotReported",
    "redox_couple": "SecondReduction",
    "quote": "The half-wave potential E1/2 shifted to \u22120.85 V vs Ag/AgCl at 0.66 M ethanol",
}


@pytest.fixture(scope="module")
def vocab() -> Vocabulary:
    return load(VOCAB_TTL)


def run(vocab: Vocabulary, **parts: Sequence[Mapping[str, object]]) -> Checked:
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [CONDITION], "measurements": [], "observations": []} | parts
    )
    return check(record, split_pages(PAPER), vocab)


def problems(checked: Checked) -> list[Problem]:
    return [p for d in checked.dropped for p in d.problems]


def test_good_record_is_kept_with_the_page_found_by_the_code(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL])
    assert not checked.dropped
    assert [m.page for m in checked.measurements] == [2]
    assert [c.page for c in checked.compounds] == [1]


def test_unicode_minus_in_text_matches_ascii_minus_in_value(vocab: Vocabulary) -> None:
    ascii_quote = POTENTIAL | {"quote": "shifted to -0.85 V vs Ag/AgCl at 0.66 M ethanol"}
    assert not run(vocab, measurements=[ascii_quote]).dropped


def test_wrong_sign_is_refused(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"value": 0.85}])
    assert any(isinstance(p, ValueNotInQuote) for p in problems(checked))
    assert not checked.measurements


def test_wrong_scale_is_refused(vocab: Vocabulary) -> None:
    quote = "Energy consumption fell from 73.43 to 50.94 kJ/mol."
    bad = POTENTIAL | {
        "property": "EnergyConsumption",
        "unit": "KJPerMol",
        "value": 5.094,
        "quote": quote,
        "redox_couple": None,
    }
    assert any(isinstance(p, ValueNotInQuote) for p in problems(run(vocab, measurements=[bad])))


def test_paraphrased_quote_is_refused_and_nothing_is_saved(vocab: Vocabulary) -> None:
    bad = POTENTIAL | {"quote": "the half wave potential moved to minus 0.85 volts against silver chloride"}
    checked = run(vocab, measurements=[bad])
    assert any(isinstance(p, QuoteNotFound) for p in problems(checked))
    assert not checked.measurements


def test_quote_spanning_two_pages_is_refused() -> None:
    across = "in acetonitrile. The half-wave potential E1/2 shifted"
    assert find_quote(split_pages(PAPER), across).__class__.__name__ == "QuoteMissing"


def test_hyphenated_line_break_is_joined() -> None:
    assert find_quote(split_pages(PAPER), "Supersaturated solutions were avoided").__class__.__name__ == "QuoteFound"


def test_unit_must_be_allowed_for_the_property(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"unit": "KJPerMol"}])
    assert any(isinstance(p, UnitNotAllowed) for p in problems(checked))


def test_potential_without_redox_couple_is_refused(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"redox_couple": None}])
    assert any(isinstance(p, RedoxCoupleMissing) for p in problems(checked))


def test_dft_is_not_an_experiment(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"method": "DFT"}])
    assert any(isinstance(p, MethodBasisMismatch) for p in problems(checked))


def test_computation_signature_on_experiment_is_refused(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"functional": "B3LYP"}])
    assert any(isinstance(p, ComputationSignatureOnExperiment) for p in problems(checked))


def test_signature_not_in_quote_is_refused(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"basis": "Computation", "method": "DFT", "functional": "B3LYP"}])
    assert not checked.measurements


def test_unknown_vocabulary_term_is_refused(vocab: Vocabulary) -> None:
    checked = run(vocab, measurements=[POTENTIAL | {"property": "Voltage"}])
    assert any(isinstance(p, UnknownTerm) and p.term == "Voltage" for p in problems(checked))


def test_result_pointing_at_a_dropped_compound_is_refused(vocab: Vocabulary) -> None:
    bad_compound = COMPOUND | {"quote": "this sentence is not in the paper at all"}
    checked = run(vocab, compounds=[bad_compound], measurements=[POTENTIAL])
    assert any(isinstance(p, DanglingReference) for p in problems(checked))
    assert not checked.measurements


def test_compound_name_must_be_in_the_text(vocab: Vocabulary) -> None:
    checked = run(vocab, compounds=[COMPOUND | {"name": "2,6-Dihydroxyanthraquinone"}])
    assert any(isinstance(p, NameNotInText) for p in problems(checked))


def test_outcome_must_answer_its_observation_kind(vocab: Vocabulary) -> None:
    obs = {
        "compound": "paq",
        "condition": "c1",
        "kind": "BindingMode",
        "outcome": "OxygenStable",
        "quote": COMPOUND["quote"],
    }
    assert any(isinstance(p, OutcomeKindMismatch) for p in problems(run(vocab, observations=[obs])))


def test_abstract_mode_saves_no_page(vocab: Vocabulary) -> None:
    record = PaperRecord.model_validate({"compounds": [COMPOUND], "conditions": [CONDITION]})
    checked = check(record, split_pages(PAPER), vocab, abstract=True)
    assert [c.page for c in checked.compounds] == [None]


def test_model_json_with_extra_fields_is_rejected() -> None:
    with pytest.raises(ValueError, match="Extra inputs"):
        PaperRecord.model_validate(json.loads('{"compounds": [], "surprise": 1}'))


def test_two_values_for_the_same_compound_condition_and_property_are_refused(vocab: Vocabulary) -> None:
    second = POTENTIAL | {"value": -0.5, "quote": "the half-wave potential E1/2 of -0.5 V vs Ag/AgCl was also seen"}
    text = PAPER + "\n===== PAGE 3 =====\nthe half-wave potential E1/2 of -0.5 V vs Ag/AgCl was also seen\n"
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [CONDITION], "measurements": [POTENTIAL, second]}
    )
    checked = check(record, split_pages(text), vocab)
    assert any(isinstance(p, ConflictingValues) for p in problems(checked))
    assert not checked.measurements


def test_same_property_in_two_conditions_is_not_a_conflict(vocab: Vocabulary) -> None:
    second = {**CONDITION, "key": "c2", "solvent": "DMF"}
    other = POTENTIAL | {
        "condition": "c2",
        "value": -1.0,
        "quote": "half-wave potential of -1.0 V vs Ag/AgCl was measured",
    }
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [CONDITION, second], "measurements": [POTENTIAL, other]}
    )
    checked = check(
        record,
        split_pages(
            PAPER.replace(
                "at 0.66 M ethanol, and",
                "at 0.66 M ethanol, and a half-wave potential of -1.0 V vs Ag/AgCl was measured; ",
            )
        ),
        vocab,
    )
    assert len(checked.measurements) == 2


def test_unspecified_condition_is_allowed_and_recorded(vocab: Vocabulary) -> None:
    dft = {
        "compound": "paq",
        "condition": "unspecified",
        "property": "BindingEnergy",
        "value": 50.94,
        "unit": "KJPerMol",
        "basis": "Computation",
        "method": "DFT",
        "quote": "Energy consumption fell from 73.43 to 50.94 kJ/mol.",
    }
    checked = run(vocab, measurements=[dft])
    assert not checked.dropped
    assert [c.item.key for c in checked.conditions if c.item.key == "unspecified"] == ["unspecified"]


def test_oxygen_couple_potential_is_not_a_quinone_potential(vocab: Vocabulary) -> None:
    quote = "the half-wave potential E1/2(O2/O2\u2022\u2212) value of the O2/O2\u2022\u2212 couples was -0.83 V"
    text = PAPER + "\n" + quote
    record = PaperRecord.model_validate(
        {
            "compounds": [COMPOUND],
            "conditions": [CONDITION],
            "measurements": [POTENTIAL | {"value": -0.83, "quote": quote}],
        }
    )
    checked = check(record, split_pages(text), vocab)
    assert any(isinstance(p, OtherSpeciesPotential) for p in problems(checked))


def test_prime_and_apostrophe_are_the_same_character() -> None:
    pages = split_pages("===== PAGE 1 =====\nwe made 1-butyl-3-((2\u2032-anthraquinoyl)methyl)imidazolium salt here")
    assert find_quote(pages, "1-butyl-3-((2'-anthraquinoyl)methyl)imidazolium salt").__class__.__name__ == "QuoteFound"


def test_refusal_shows_where_the_quote_first_differs() -> None:
    pages = split_pages("===== PAGE 1 =====\nthe rate constant was measured in dimethyl sulfoxide at room temperature")
    result = find_quote(pages, "the rate constant was measured in DMF at room temperature")
    assert isinstance(result, QuoteMissing)
    assert "imethylsulfoxide" in result.closest
    assert "you wrote 'mfat" in result.closest


def test_hyphen_at_a_line_break_matches_with_or_without_it() -> None:
    pages = split_pages("===== PAGE 1 =====\nsynthesized 1-\nbutyl-3-methylimidazolium and the [BAQMIM]-\n[TFSA] salt")
    assert isinstance(find_quote(pages, "1-butyl-3-methylimidazolium"), QuoteFound)
    assert isinstance(find_quote(pages, "1butyl-3-methylimidazolium"), QuoteFound)
    assert isinstance(find_quote(pages, "the [BAQMIM][TFSA] salt"), QuoteFound)
    assert isinstance(find_quote(pages, "the [BAQMIM]-[TFSA] salt"), QuoteFound)


def test_a_minus_sign_is_not_treated_as_a_hyphen() -> None:
    pages = split_pages("===== PAGE 1 =====\nthe peak shifted to -0.85 V versus the reference")
    assert isinstance(find_quote(pages, "the peak shifted to -0.85 V versus the reference"), QuoteFound)
    assert isinstance(find_quote(pages, "the peak shifted to 0.85 V versus the reference"), QuoteMissing)
    pages = split_pages("===== PAGE 1 =====\nthe peak shifted to 0.85 V versus the reference")
    assert isinstance(find_quote(pages, "the peak shifted to -0.85 V versus the reference"), QuoteMissing)


def test_short_compound_name_present_in_the_text_is_accepted(vocab: Vocabulary) -> None:
    short = COMPOUND | {"name": "quinone", "quote": "9,10-Phenanthrenequinone (PAQ) was studied in acetonitrile."}
    checked = run(vocab, compounds=[short])
    assert not any(isinstance(p, NameNotInText) for p in problems(checked))


def test_ligature_characters_match_their_letters() -> None:
    pages = split_pages("===== PAGE 1 =====\nbis(tri\ufb02uoromethylsulfonyl)imide was puri\ufb01ed at o\ufb00 peak")
    assert isinstance(find_quote(pages, "bis(trifluoromethylsulfonyl)imide was purified at off peak"), QuoteFound)
    assert contains(pages, "trifluoromethylsulfonyl")


def test_private_use_ligatures_from_some_pdfs_match_their_letters() -> None:
    pages = split_pages(
        "===== PAGE 1 =====\nbis(tri\ue104uoromethyl sulfonyl)imide, modi\ue103ed gra\ue09dis, a \ue104ow cell"
    )
    assert isinstance(find_quote(pages, "bis(trifluoromethylsulfonyl)imide, modified graftis, a flow cell"), QuoteFound)


def _measurement_text(quote_sentence: str) -> str:
    return PAPER + "\n===== PAGE 3 =====\n" + quote_sentence + "\n"


def _check_one(vocab: Vocabulary, sentence: str, **changes: object) -> Checked:
    base = POTENTIAL | {"quote": sentence}
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [CONDITION], "measurements": [base | changes]}
    )
    return check(record, split_pages(_measurement_text(sentence)), vocab)


def test_concentration_is_not_a_capacity_in_mol_per_mol(vocab: Vocabulary) -> None:
    sentence = "provide a volumetric quinone concentration of at least 1.1 M (2.2 M CO2 capacity)."
    checked = _check_one(vocab, sentence, property="CaptureCapacity", unit="MolPerMol", value=2.2, redox_couple=None)
    assert any(isinstance(p, UnitNotInQuote) for p in problems(checked))


def test_first_order_rate_constant_is_not_a_second_order_one(vocab: Vocabulary) -> None:
    sentence = (
        "The corresponding standard rate constants at these formal potentials are 1.3 and 0.8 s\u22121, respectively."
    )
    checked = _check_one(
        vocab, sentence, property="RateConstant", unit="PerMolarPerSecond", value=0.8, redox_couple=None
    )
    assert any(isinstance(p, UnitNotInQuote) for p in problems(checked))


def test_matching_printed_unit_is_accepted(vocab: Vocabulary) -> None:
    sentence = "the bimolecular rate constant is 162 M\u22121 s\u22121 in 100 mM NBu4ClO4"
    checked = _check_one(
        vocab, sentence, property="RateConstant", unit="PerMolarPerSecond", value=162, redox_couple=None
    )
    assert not checked.dropped


def test_table_row_without_a_printed_unit_is_accepted(vocab: Vocabulary) -> None:
    sentence = "TCNQ 12.5 0.31 4.80"
    checked = _check_one(vocab, sentence, property="EnergyConsumption", unit="KJPerMol", value=12.5, redox_couple=None)
    assert not checked.dropped


def test_wrong_energy_unit_is_refused(vocab: Vocabulary) -> None:
    sentence = "The complexation energies are \u22123.87 kcal/mol for the first salt."
    checked = _check_one(
        vocab,
        sentence,
        property="BindingEnergy",
        unit="KJPerMol",
        value=-3.87,
        redox_couple=None,
        basis="Computation",
        method="DFT",
    )
    assert any(isinstance(p, UnitNotInQuote) for p in problems(checked))


def test_activation_barrier_is_not_a_binding_energy(vocab: Vocabulary) -> None:
    sentence = "DFT predicts \u0394G\u2021 values of 0.331 and 0.275 eV for AQ and PAQ, respectively."
    checked = _check_one(
        vocab,
        sentence,
        property="BindingEnergy",
        unit="ElectronVolt",
        value=0.275,
        redox_couple=None,
        basis="Computation",
        method="DFT",
    )
    assert any(isinstance(p, OtherQuantity) for p in problems(checked))


def test_power_of_ten_must_be_part_of_the_value(vocab: Vocabulary) -> None:
    sentence = (
        "binding constants of AQ-Cl and AQ-COO-C3H7 were 2.35 \u00d7 105 and 7.78 \u00d7 107 M\u22121, respectively."
    )
    kw = {"property": "BindingConstant", "unit": "PerMolar", "redox_couple": None}
    assert any(isinstance(p, ScaleNotApplied) for p in problems(_check_one(vocab, sentence, value=2.35, **kw)))
    assert not _check_one(vocab, sentence, value=2.35e5, **kw).dropped
    assert not _check_one(vocab, sentence, value=7.78e7, **kw).dropped


def test_negative_power_of_ten_is_applied_too(vocab: Vocabulary) -> None:
    sentence = "the standard rate constant is 4.5 \u00d7 10\u22123 M\u22121 s\u22121 for this quinone"
    kw = {"property": "RateConstant", "unit": "PerMolarPerSecond", "redox_couple": None}
    assert any(isinstance(p, ScaleNotApplied) for p in problems(_check_one(vocab, sentence, value=4.5, **kw)))
    assert not _check_one(vocab, sentence, value=4.5e-3, **kw).dropped


def test_end_of_a_between_range_is_not_a_measurement(vocab: Vocabulary) -> None:
    sentence = "The experiments at 0.5 mL/min demonstrated energetics between 35 and 220 kJ/mol."
    kw = {"property": "EnergyConsumption", "unit": "KJPerMol", "redox_couple": None}
    assert any(isinstance(p, RangeBound) for p in problems(_check_one(vocab, sentence, value=220, **kw)))


def test_from_x_to_y_between_two_states_is_not_a_range(vocab: Vocabulary) -> None:
    sentence = "Energy consumption decreased from 86.1 kJ mol\u22121 (bulk) to 66.7 kJ mol\u22121 (in-situ)"
    kw = {"property": "EnergyConsumption", "unit": "KJPerMol", "redox_couple": None}
    assert not _check_one(vocab, sentence, value=66.7, **kw).dropped


def test_gigajoule_per_ton_is_not_kilojoule_per_mole(vocab: Vocabulary) -> None:
    sentence = "increasing only slightly to 5.85 GJ/ton and 1.63 GJ/ton, respectively, in flue gas"
    kw = {"property": "EnergyConsumption", "unit": "KJPerMol", "redox_couple": None}
    assert any(isinstance(p, UnitNotInQuote) for p in problems(_check_one(vocab, sentence, value=1.63, **kw)))


def test_capture_efficiency_is_not_faradaic_efficiency(vocab: Vocabulary) -> None:
    kw = {"property": "FaradaicEfficiency", "unit": "Percent", "redox_couple": None}
    bad = "Finally, it demonstrated superior capture efficiency (43.7%), volumetric capacity (5.6 kg m-3)"
    assert any(isinstance(p, OtherQuantity) for p in problems(_check_one(vocab, bad, value=43.7, **kw)))
    good = "The cell reached a Faradaic efficiency of 87% and a capture efficiency of 90%"
    assert not _check_one(vocab, good, value=87, **kw).dropped


def test_a_bound_is_not_a_measured_value(vocab: Vocabulary) -> None:
    kw = {"property": "BindingConstant", "unit": "PerMolar", "redox_couple": None}
    for sentence in (
        "yields a RAQCO2 binding constant K1 less than 0.5",
        "a binding constant of > 0.5 M\u22121 was estimated",
        "binding constant of at most 0.5 M\u22121 for this quinone",
    ):
        assert any(isinstance(p, BoundNotValue) for p in problems(_check_one(vocab, sentence, value=0.5, **kw))), (
            sentence
        )


def test_a_plain_value_after_similar_words_is_fine(vocab: Vocabulary) -> None:
    kw = {"property": "BindingConstant", "unit": "PerMolar", "redox_couple": None}
    sentence = "the binding constant was 0.5 M\u22121, which is less than that of the other quinone"
    assert not _check_one(vocab, sentence, value=0.5, **kw).dropped


def test_areal_capacity_is_not_a_capacity_per_gram(vocab: Vocabulary) -> None:
    kw = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None}
    sentence = "an areal capacity at \u22481.6 \u03bcmol cm\u22122 within 60 min"
    assert any(isinstance(p, UnitNotInQuote) for p in problems(_check_one(vocab, sentence, value=1.6, **kw)))


def _ctx_check(
    vocab: Vocabulary,
    page_sentence: str,
    quote: str,
    fields: Mapping[str, object] | None = None,
    cond: Mapping[str, object] | None = None,
) -> Checked:
    base = {**POTENTIAL, "quote": quote, **(fields or {})}
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [{**CONDITION, **(cond or {})}], "measurements": [base]}
    )
    return check(record, split_pages(PAPER + "\n===== PAGE 3 =====\n" + page_sentence + "\n"), vocab)


def test_a_clipped_quote_cannot_hide_an_activation_barrier(vocab: Vocabulary) -> None:
    page = "Analogously, DFT predicts \u0394G\u2021 values of 0.331 and 0.275 eV for AQ and PAQ, respectively."
    fields = {
        "property": "BindingEnergy",
        "unit": "ElectronVolt",
        "value": 0.275,
        "redox_couple": None,
        "basis": "Computation",
        "method": "DFT",
    }
    checked = _ctx_check(vocab, page, "0.275 eV for AQ and PAQ, respectively", fields)
    assert any(isinstance(p, OtherQuantity) for p in problems(checked))


def test_a_clipped_quote_cannot_hide_an_oxygen_couple(vocab: Vocabulary) -> None:
    page = "the O2/O2 radical anion couple has a potential of \u22120.83 V vs Ag/AgCl in this medium."
    checked = _ctx_check(vocab, page, "of \u22120.83 V vs Ag/AgCl in this medium", {"value": -0.83})
    assert any(isinstance(p, OtherSpeciesPotential) for p in problems(checked))


def test_reference_electrode_named_in_the_quote_must_match_the_condition(vocab: Vocabulary) -> None:
    page = "The half-wave potential was \u22120.45 V vs NHE for this quinone."
    checked = _ctx_check(vocab, page, "half-wave potential was \u22120.45 V vs NHE", {"value": -0.45})
    assert any(isinstance(p, ReferenceContradicts) for p in problems(checked))
    ok = _ctx_check(
        vocab, page, "half-wave potential was \u22120.45 V vs NHE", {"value": -0.45}, {"reference_electrode": "SHE"}
    )
    assert not ok.dropped


def test_binding_measured_under_an_inert_atmosphere_is_a_contradiction(vocab: Vocabulary) -> None:
    page = "The binding constant was 9.3 under 100% CO2 for this quinone."
    kw = {"property": "Log10BindingConstant", "unit": "Dimensionless", "redox_couple": None, "value": 9.3}
    bad = _ctx_check(vocab, page, "binding constant was 9.3 under 100% CO2", kw, {"atmosphere": "Inert"})
    assert any(isinstance(p, AtmosphereContradicts) for p in problems(bad))
    good = _ctx_check(vocab, page, "binding constant was 9.3 under 100% CO2", kw, {"atmosphere": "CO2Atmosphere"})
    assert not good.dropped


def test_theoretical_value_is_not_an_experiment(vocab: Vocabulary) -> None:
    page = "a theoretical capacity of 8.4 mmol g\u22121 can be achieved"
    kw = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None, "value": 8.4}
    bad = _ctx_check(vocab, page, "theoretical capacity of 8.4 mmol g\u22121", kw)
    assert any(isinstance(p, ProvenanceMismatch) for p in problems(bad))
    ok = _ctx_check(
        vocab, page, "theoretical capacity of 8.4 mmol g\u22121", {**kw, "basis": "Computation", "method": "DFT"}
    )
    assert not ok.dropped


def test_a_label_number_is_not_a_measurement(vocab: Vocabulary) -> None:
    page = "the species in state 1 were compared with those in state 2 at the same potential"
    kw = {"property": "BindingConstant", "unit": "PerMolar", "redox_couple": None, "value": 1}
    checked = _ctx_check(vocab, page, "species in state 1 were compared", kw)
    assert any(isinstance(p, UnrelatedNumber) for p in problems(checked))


def test_per_square_molar_and_total_amounts_are_not_per_molar_or_per_gram(vocab: Vocabulary) -> None:
    kw = {"property": "BindingConstant", "unit": "PerMolar", "redox_couple": None, "value": 7.3e21}
    assert any(
        isinstance(p, UnitNotInQuote)
        for p in problems(_check_one(vocab, "a value of 7.3 \u00d7 1021 M\u22122 was found", **kw))
    )
    cap = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None, "value": 0.187}
    assert any(
        isinstance(p, UnitNotInQuote)
        for p in problems(_check_one(vocab, "a total capture of 0.187 mmol was reached", **cap))
    )


def test_ranges_from_x_to_y_are_ranges(vocab: Vocabulary) -> None:
    kw = {"property": "EnergyConsumption", "unit": "KJPerMol", "redox_couple": None, "value": 220}
    sentence = "the energy consumption ranges from 35 to 220 kJ/mol depending on the flow"
    assert any(isinstance(p, RangeBound) for p in problems(_check_one(vocab, sentence, **kw)))


def _obs_check(vocab: Vocabulary, quote: str, kind: str, outcome: str, atmosphere: str = "AirOxygen") -> Checked:
    obs = {"compound": "paq", "condition": "c1", "kind": kind, "outcome": outcome, "quote": quote}
    record = PaperRecord.model_validate(
        {"compounds": [COMPOUND], "conditions": [CONDITION | {"atmosphere": atmosphere}], "observations": [obs]}
    )
    return check(record, split_pages(PAPER + "\n===== PAGE 3 =====\n" + quote + "\n"), vocab)


def test_observation_needs_evidence_for_its_outcome(vocab: Vocabulary) -> None:
    stable = _obs_check(
        vocab, "the reduced quinone degrades rapidly in the presence of oxygen", "OxygenStability", "OxygenStable"
    )
    assert any(isinstance(p, EvidenceMissing) for p in problems(stable))
    good = _obs_check(
        vocab,
        "the reduced quinone remains stable in the presence of oxygen over ten cycles",
        "OxygenStability",
        "OxygenStable",
    )
    assert not good.dropped
    bi = _obs_check(vocab, "the dianion binds CO2 as a biscarbonate species in solution", "BindingMode", "Bicarbonate")
    assert any(isinstance(p, EvidenceMissing) for p in problems(bi))


def test_observation_atmosphere_must_fit_the_kind(vocab: Vocabulary) -> None:
    quote = "the reduced quinone remains stable in the presence of oxygen over ten cycles"
    bad = _obs_check(vocab, quote, "OxygenStability", "OxygenStable", atmosphere="Inert")
    assert any(isinstance(p, AtmosphereContradicts) for p in problems(bad))


def test_oxygen_outcome_needs_the_quote_to_mention_oxygen(vocab: Vocabulary) -> None:
    quote = "the reduced quinone remains unchanged over ten consecutive cycles"
    checked = _obs_check(vocab, quote, "OxygenStability", "OxygenStable")
    assert any(isinstance(p, EvidenceMissing) for p in problems(checked))


def test_direct_air_capture_is_not_an_oxygen_statement(vocab: Vocabulary) -> None:
    quote = "1 is unlikely to serve as an adequate direct air capture sorbent due to atmospheric water"
    checked = _obs_check(vocab, quote, "OxygenStability", "OxygenUnstable")
    assert any(isinstance(p, EvidenceMissing) for p in problems(checked))
    ok = _obs_check(
        vocab, "the reduced quinone reacts rapidly with O2 and is oxidised back", "OxygenStability", "OxygenUnstable"
    )
    assert not any(isinstance(p, EvidenceMissing) for p in problems(ok))


def test_a_value_followed_by_a_citation_is_not_the_papers_own(vocab: Vocabulary) -> None:
    kw = {"property": "ReductionPotential", "unit": "Volt", "value": -1.21, "redox_couple": "SecondReduction"}
    bad = _ctx_check(vocab, "E \u25e6 2 V \u22121.21 [10]", "E \u25e6 2 V \u22121.21 [10]", kw)
    assert any(isinstance(p, CitedValue) for p in problems(bad))
    own = "the second reduction appeared at \u22121.21 V vs Ag/AgCl in this work"
    assert not _ctx_check(vocab, own, own, kw).dropped


def test_computation_needs_a_method_or_theory_wording(vocab: Vocabulary) -> None:
    page = "Li2CO3 was collected, corresponding to a CO2 capture faradaic efficiency of 67%."
    kw = {
        "property": "FaradaicEfficiency",
        "unit": "Percent",
        "value": 67,
        "redox_couple": None,
        "basis": "Computation",
        "method": "NotReported",
    }
    assert any(isinstance(p, ComputationWithoutEvidence) for p in problems(_ctx_check(vocab, page, page, kw)))
    dft = {**kw, "method": "DFT"}
    assert not any(isinstance(p, ComputationWithoutEvidence) for p in problems(_ctx_check(vocab, page, page, dft)))


THEORY_PAGE = (
    "The theoretical capacity is 12 mmol g\u22121 but the measured capacity reached only 8.4 mmol g\u22121 in practice."
)


def test_theoretical_wording_elsewhere_in_the_sentence_does_not_reject_a_measured_value(vocab: Vocabulary) -> None:
    page = THEORY_PAGE
    kw = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None, "value": 8.4}
    checked = _ctx_check(vocab, page, "measured capacity reached only 8.4 mmol g\u22121 in practice", kw)
    assert not any(isinstance(p, ProvenanceMismatch) for p in problems(checked))


def test_theoretical_wording_right_before_the_value_still_rejects_it(vocab: Vocabulary) -> None:
    page = THEORY_PAGE
    kw = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None, "value": 12}
    checked = _ctx_check(vocab, page, "The theoretical capacity is 12 mmol g\u22121", kw)
    assert any(isinstance(p, ProvenanceMismatch) for p in problems(checked))


def test_theoretical_wording_far_before_the_value_does_not_reject_it(vocab: Vocabulary) -> None:
    page = (
        "A theoretical model exists, and the cell was run with a 0.1 M electrolyte, "
        "giving a capacity of 8.4 mmol g\u22121 here."
    )
    kw = {"property": "CaptureCapacity", "unit": "MmolPerGram", "redox_couple": None, "value": 8.4}
    checked = _ctx_check(vocab, page, "giving a capacity of 8.4 mmol g\u22121 here", kw)
    assert not any(isinstance(p, ProvenanceMismatch) for p in problems(checked))


def test_a_comma_after_a_number_is_not_a_decimal_point() -> None:
    assert numbers_in("values of 12, 15 and 3,5 were seen") == (12.0, 15.0, 3.5)
    heads = before_value("the theoretical model, giving 8.4 mmol", 8.4, 60)
    assert heads == ["the theoretical model, giving "]
