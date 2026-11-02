"""The checker: keeps what is backed by the text and the vocabulary, drops the rest with a typed reason."""

import re
from dataclasses import dataclass

from .record import CompoundRec, ConditionRec, MeasurementRec, ObservationRec, PaperRecord
from .text import (
    Page,
    QuoteFound,
    QuoteMissing,
    after_value,
    before_value,
    contains,
    context_of,
    find_quote,
    numbers_in,
    powers_in,
)
from .vocab import Term, Vocabulary


@dataclass(frozen=True, slots=True)
class QuoteNotFound:
    """The quote is not on any page."""

    where: str
    closest: str


@dataclass(frozen=True, slots=True)
class ValueNotInQuote:
    """The value is not printed in its quote (sign and scale errors land here)."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class UnknownTerm:
    """A controlled field holds something outside its scheme."""

    where: str
    scheme: str
    term: str


@dataclass(frozen=True, slots=True)
class UnitNotAllowed:
    """The unit is not allowed for the property."""

    where: str
    prop: str
    unit: str
    allowed: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RedoxCoupleMissing:
    """A potential must name its reduction step."""

    where: str


@dataclass(frozen=True, slots=True)
class MethodBasisMismatch:
    """The method does not belong to the basis."""

    where: str
    method: str
    basis: str


@dataclass(frozen=True, slots=True)
class OutcomeKindMismatch:
    """The outcome does not answer the observation kind."""

    where: str
    outcome: str
    kind: str


@dataclass(frozen=True, slots=True)
class DanglingReference:
    """A result points at a compound or condition that is missing or was dropped."""

    where: str
    key: str


@dataclass(frozen=True, slots=True)
class NameNotInText:
    """A compound name is nowhere in the text."""

    where: str
    name: str


@dataclass(frozen=True, slots=True)
class ConflictingValues:
    """The same compound, condition and property carries different values: the conditions are not told apart."""

    where: str
    prop: str
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class OtherSpeciesPotential:
    """The potential belongs to another couple (for example O2/O2 radical anion), not to the compound."""

    where: str


@dataclass(frozen=True, slots=True)
class MalformedItem:
    """The item does not have the required shape (missing field, wrong type, quote too long)."""

    where: str
    message: str


@dataclass(frozen=True, slots=True)
class UnitNotInQuote:
    """A different unit is printed right after the value than the one that was saved."""

    where: str
    saved: str
    printed: str


@dataclass(frozen=True, slots=True)
class OtherQuantity:
    """The quote is about another quantity (for example an activation barrier), not the saved property."""

    where: str
    prop: str
    word: str


@dataclass(frozen=True, slots=True)
class ScaleNotApplied:
    """The quote prints "a x 10^n" but only the mantissa was saved."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class RangeBound:
    """The value is one end of a "between A and B" range, not a measurement of a named compound."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class BoundNotValue:
    """The quote gives the value as a bound (less than, more than, at least, ...), not as a measurement."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class AtmosphereContradicts:
    """The condition's atmosphere cannot hold for this result (CO2 binding under an inert atmosphere, ...)."""

    where: str
    atmosphere: str
    what: str


@dataclass(frozen=True, slots=True)
class ReferenceContradicts:
    """The quote names a reference electrode other than the one in the condition."""

    where: str
    saved: str
    printed: str


@dataclass(frozen=True, slots=True)
class ProvenanceMismatch:
    """The text calls the value theoretical or simulated but it was saved as an experiment."""

    where: str
    word: str


@dataclass(frozen=True, slots=True)
class UnrelatedNumber:
    """The number is a label (state 1, Table 2, step 3), not a measurement."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class EvidenceMissing:
    """The quote does not support the saved outcome (wrong words or the opposite meaning)."""

    where: str
    outcome: str
    why: str


@dataclass(frozen=True, slots=True)
class CitedValue:
    """The value is followed by a citation marker: it is quoted from another work, not measured here."""

    where: str
    value: float


@dataclass(frozen=True, slots=True)
class ComputationWithoutEvidence:
    """The basis is Computation but neither the method nor the wording says it was computed."""

    where: str


@dataclass(frozen=True, slots=True)
class ComputationSignatureOnExperiment:
    """Method-signature text must not decorate an experimental value."""
    where: str

@dataclass(frozen=True, slots=True)
class SignatureNotInQuote:
    """A reported calculation signature is not supported by its quote."""
    where: str
    field: str


type Problem = (
    CitedValue
    | ComputationSignatureOnExperiment
    | SignatureNotInQuote
    | ComputationWithoutEvidence
    | AtmosphereContradicts
    | ReferenceContradicts
    | ProvenanceMismatch
    | UnrelatedNumber
    | EvidenceMissing
    | BoundNotValue
    | ScaleNotApplied
    | RangeBound
    | UnitNotInQuote
    | OtherQuantity
    | MalformedItem
    | ConflictingValues
    | OtherSpeciesPotential
    | QuoteNotFound
    | ValueNotInQuote
    | UnknownTerm
    | UnitNotAllowed
    | RedoxCoupleMissing
    | MethodBasisMismatch
    | OutcomeKindMismatch
    | DanglingReference
    | NameNotInText
)


def describe(problem: Problem) -> str:  # noqa: C901, PLR0912
    """One line for the model: what is wrong and what to do."""
    match problem:
        case QuoteNotFound(where=w, closest=c):
            return f"{w}: quote is not verbatim on one page. {c}"
        case ValueNotInQuote(where=w, value=v):
            return f"{w}: the number {v} is not printed in the quote; quote the sentence or table row that prints it"
        case UnknownTerm(where=w, scheme=s, term=t):
            return f"{w}: '{t}' is not a term of {s}"
        case UnitNotAllowed(where=w, prop=p, unit=u, allowed=a):
            return f"{w}: unit '{u}' is not allowed for {p}; allowed: {', '.join(a)}"
        case RedoxCoupleMissing(where=w):
            return f"{w}: a potential needs redox_couple (FirstReduction, SecondReduction, TwoElectron or NotReported)"
        case MethodBasisMismatch(where=w, method=m, basis=b):
            return f"{w}: method {m} does not fit basis {b}"
        case OutcomeKindMismatch(where=w, outcome=o, kind=k):
            return f"{w}: outcome {o} does not answer observation kind {k}"
        case DanglingReference(where=w, key=k):
            return f"{w}: refers to '{k}', which is not a kept compound or condition"
        case NameNotInText(where=w, name=n):
            return f"{w}: the name '{n}' is not in the text"
        case CitedValue(where=w, value=v):
            return f"{w}: {v} is followed by a citation marker, so it is another work's value or a model input; omit it"
        case ComputationWithoutEvidence(where=w):
            return (
                f"{w}: basis Computation needs method DFT or MolecularDynamics, "
                "or wording such as calculated or simulated"
            )
        case ComputationSignatureOnExperiment(where=w):
            return f"{w}: computational method signatures are not allowed on an experiment"
        case SignatureNotInQuote(where=w, field=f):
            return f"{w}: {f} is not printed in the quote; omit it or quote the calculation-method text"
        case AtmosphereContradicts(where=w, atmosphere=a, what=x):
            return f"{w}: atmosphere {a} contradicts {x}; use CO2Atmosphere, FlueGas, AirOxygen or NotReported"
        case ReferenceContradicts(where=w, saved=s, printed=p):
            return (
                f"{w}: the quote names reference '{p}' but the condition says {s}; "
                "make a condition with the printed reference"
            )
        case ProvenanceMismatch(where=w, word=k):
            return f"{w}: the text says '{k}', so basis must be Computation, not Experiment"
        case UnrelatedNumber(where=w, value=v):
            return f"{w}: {v} is a label such as 'state 1' or 'Table 2', not a measurement"
        case EvidenceMissing(where=w, outcome=o, why=y):
            return f"{w}: the quote does not support {o}: {y}"
        case BoundNotValue(where=w, value=v):
            return f"{w}: {v} is given as a bound (less than, more than, at least, ...) in the quote; omit it"
        case ScaleNotApplied(where=w, value=v):
            return f"{w}: the quote prints {v} x 10^n; save the full number (for example 2.35e5), not the mantissa"
        case RangeBound(where=w, value=v):
            return f"{w}: {v} is one end of a range in the quote; record values of named compounds, not ranges"
        case UnitNotInQuote(where=w, saved=s, printed=p):
            return (
                f"{w}: the quote prints '{p}' after the value, which is not the saved unit {s}; "
                "fix the unit or omit the item"
            )
        case OtherQuantity(where=w, prop=p, word=k):
            return f"{w}: the quote is about '{k}', which is not {p}; omit it"
        case MalformedItem(where=w, message=m):
            return f"{w}: wrong shape: {m}"
        case ConflictingValues(where=w, prop=p, values=v):
            listed = ", ".join(str(x) for x in v)
            return (
                f"{w}: {p} has different values ({listed}) for the same compound and condition. "
                "Make one condition per value (pH, salt, additive or solvent) and give each value its own condition key"
            )
        case OtherSpeciesPotential(where=w):
            return f"{w}: this potential belongs to another couple (such as O2/O2 radical anion); omit it"


@dataclass(frozen=True, slots=True)
class Located[T]:
    """A kept item with the page its quote was found on (None for abstract text)."""

    item: T
    page: int | None


@dataclass(frozen=True, slots=True)
class Dropped:
    """An item that failed the checker, as the model sent it, with its reasons."""

    kind: str
    raw: str
    problems: tuple[Problem, ...]


@dataclass(frozen=True, slots=True)
class Checked:
    """Result of checking one record."""

    compounds: tuple[Located[CompoundRec], ...]
    conditions: tuple[Located[ConditionRec], ...]
    measurements: tuple[Located[MeasurementRec], ...]
    observations: tuple[Located[ObservationRec], ...]
    dropped: tuple[Dropped, ...]


def _quote(pages: tuple[Page, ...], quote: str, where: str, *, abstract: bool) -> tuple[int | None, list[Problem]]:
    match find_quote(pages, quote):
        case QuoteFound(page=p):
            return (None if abstract else p), []
        case QuoteMissing(closest=c):
            return None, [QuoteNotFound(where=where, closest=c)]


def _in(vocab: Vocabulary, scheme: str, term: str, where: str) -> list[Problem]:
    return [] if vocab.allows(scheme, term) else [UnknownTerm(where=where, scheme=scheme, term=term)]


def check(record: PaperRecord, pages: tuple[Page, ...], vocab: Vocabulary, *, abstract: bool = False) -> Checked:
    """Keep the items the text and the vocabulary back; drop the others with their problems."""
    dropped: list[Dropped] = []
    haystack = "".join(p.text for p in pages)
    compounds: list[Located[CompoundRec]] = []
    for i, c in enumerate(record.compounds):
        where = f"compounds[{i}] {c.key}"
        page, problems = _quote(pages, c.quote, where, abstract=abstract)
        problems += _in(vocab, "Skeleton", c.skeleton, where) + _in(vocab, "Form", c.form, where)
        problems += [p for s in c.substituent_classes for p in _in(vocab, "SubstituentClass", s, where)]
        if not contains(pages, c.name):
            problems.append(NameNotInText(where=where, name=c.name))
        _keep_or_drop(problems, c, page, "compound", compounds, dropped)
    kept_compounds = {c.item.key for c in compounds}
    conditions: list[Located[ConditionRec]] = []
    for i, k in enumerate(record.conditions):
        where = f"conditions[{i}] {k.key}"
        page, problems = _quote(pages, k.quote, where, abstract=abstract)
        problems += _in(vocab, "Solvent", k.solvent, where)
        problems += _in(vocab, "ReferenceElectrode", k.reference_electrode, where)
        problems += _in(vocab, "Atmosphere", k.atmosphere, where)
        _keep_or_drop(problems, k, page, "condition", conditions, dropped)
    kept_conditions = {k.item.key for k in conditions} | {UNSPECIFIED}
    cond_of = {k.item.key: k.item for k in conditions}
    measurements: list[Located[MeasurementRec]] = []
    for i, m in enumerate(record.measurements):
        where = f"measurements[{i}] {m.compound}/{m.property}"
        page, problems = _quote(pages, m.quote, where, abstract=abstract)
        problems += _check_measurement(m, vocab, where, kept_compounds, kept_conditions)
        problems += _check_context(m, context_of(pages, m.quote), cond_of.get(m.condition), where)
        if not any(abs(n - m.value) < 1e-9 for n in numbers_in(m.quote)):
            problems.append(ValueNotInQuote(where=where, value=m.value))
        _keep_or_drop(problems, m, page, "measurement", measurements, dropped)
    observations: list[Located[ObservationRec]] = []
    for i, o in enumerate(record.observations):
        where = f"observations[{i}] {o.compound}/{o.kind}"
        page, problems = _quote(pages, o.quote, where, abstract=abstract)
        problems += _check_observation(o, vocab, where, kept_compounds, kept_conditions)
        problems += _check_evidence(o, cond_of.get(o.condition), where)
        _keep_or_drop(problems, o, page, "observation", observations, dropped)
    del haystack
    measurements, conflicts = _split_conflicts(measurements)
    dropped += conflicts
    uses_unspecified = any(x.item.condition == UNSPECIFIED for x in [*measurements, *observations])
    if uses_unspecified:
        conditions.append(Located(item=_unspecified_condition(), page=None))
    return Checked(tuple(compounds), tuple(conditions), tuple(measurements), tuple(observations), tuple(dropped))


def _unspecified_condition() -> ConditionRec:
    return ConditionRec(
        key=UNSPECIFIED,
        solvent="NotReported",
        reference_electrode="NotReported",
        atmosphere="NotReported",
        quote="(condition not stated in the paper)",
    )


def _split_conflicts(
    kept: list[Located[MeasurementRec]],
) -> tuple[list[Located[MeasurementRec]], list[Dropped]]:
    groups: dict[tuple[str, str, str, str | None], list[Located[MeasurementRec]]] = {}
    for loc in kept:
        m = loc.item
        groups.setdefault((m.compound, m.condition, m.property, m.redox_couple), []).append(loc)
    ok: list[Located[MeasurementRec]] = []
    dropped: list[Dropped] = []
    for (compound, condition, prop, _), members in groups.items():
        values = tuple(sorted({x.item.value for x in members}))
        if len(values) < 2:
            ok += members
            continue
        problem = ConflictingValues(where=f"measurements {compound}/{condition}/{prop}", prop=prop, values=values)
        dropped += [Dropped(kind="measurement", raw=x.item.model_dump_json(), problems=(problem,)) for x in members]
    return ok, dropped


def _keep_or_drop[T: CompoundRec | ConditionRec | MeasurementRec | ObservationRec](
    problems: list[Problem], item: T, page: int | None, kind: str, kept: list[Located[T]], dropped: list[Dropped]
) -> None:
    if problems:
        dropped.append(Dropped(kind=kind, raw=item.model_dump_json(), problems=tuple(problems)))
    else:
        kept.append(Located(item=item, page=page))


UNSPECIFIED = "unspecified"
_M1 = r"M\s*(?:-|\u2212)\s*1"
_PRINTED_UNITS: tuple[tuple[str, re.Pattern[str], frozenset[str]], ...] = (
    ("M^-1 s^-1", re.compile(rf"^\s*{_M1}\s*s\s*(?:-|\u2212)\s*1"), frozenset({"PerMolarPerSecond"})),
    ("s^-1", re.compile(r"^\s*s\s*(?:-|\u2212)\s*1"), frozenset()),
    ("M^-1", re.compile(rf"^\s*(?:{_M1}|L\s*mol\s*(?:-|\u2212)?\s*1)"), frozenset({"PerMolar"})),
    ("kJ/mol", re.compile(r"^\s*kJ\s*(?:/|\u22c5|\u00b7|\s)?\s*mol", re.IGNORECASE), frozenset({"KJPerMol"})),
    ("kcal/mol", re.compile(r"^\s*kcal\s*(?:/|\u22c5|\u00b7|\s)?\s*mol", re.IGNORECASE), frozenset({"KcalPerMol"})),
    ("eV", re.compile(r"^\s*eV\b"), frozenset({"ElectronVolt"})),
    ("mmol/g", re.compile(r"^\s*mmol\s*(?:/|\u22c5|\u00b7|\s)?\s*g", re.IGNORECASE), frozenset({"MmolPerGram"})),
    ("mol/mol", re.compile(r"^\s*mol\s*(?:CO2)?\s*(?:/|per)\s*mol", re.IGNORECASE), frozenset({"MolPerMol"})),
    ("M^-2", re.compile(r"^\s*M\s*(?:-|\u2212)\s*2"), frozenset()),
    ("total mmol", re.compile(r"^\s*mmol(?!\s*(?:/|\s)?\s*g)(?!\w)", re.IGNORECASE), frozenset()),
    (
        "per area",
        re.compile(r"^\s*(?:\u03bc|\u00b5|m|n)?mol\s*(?:/|\s)?\s*(?:cm|m)\s*(?:-|\u2212)?\s*2", re.IGNORECASE),
        frozenset(),
    ),
    ("mg/g", re.compile(r"^\s*mg\s*(?:/|\s)?\s*g", re.IGNORECASE), frozenset()),
    ("GJ/ton", re.compile(r"^\s*GJ\s*(?:/|\s)\s*t", re.IGNORECASE), frozenset()),
    ("kWh", re.compile(r"^\s*kWh", re.IGNORECASE), frozenset()),
    ("%", re.compile(r"^\s*%"), frozenset({"Percent"})),
    ("V", re.compile(r"^\s*V\b"), frozenset({"Volt"})),
    ("mV", re.compile(r"^\s*mV\b"), frozenset()),
    ("M (concentration)", re.compile(r"^\s*M\b(?!\s*(?:-|\u2212)\s*1)"), frozenset()),
)
_BOUND = re.compile(
    r"(?:less than|more than|greater than|lower than|higher than|smaller than|larger than|below|above|"
    r"at least|at most|up to|[<>\u2264\u2265])\s*[~\u2248]?\s*$",
    re.IGNORECASE,
)
_REFS = (
    ("SHE", re.compile(r"\b[NS]HE\b|hydrogen electrode")),
    ("FcFcPlus", re.compile(r"Fc\s*\+?\s*/\s*Fc|Fe\(C5H5\)2|ferrocen")),
    ("AgAgCl", re.compile(r"Ag\s*/\s*AgCl")),
    ("SCE", re.compile(r"\bSCE\b|calomel")),
    ("AgAgPlus", re.compile(r"Ag\s*/\s*Ag\s*\+|Ag\s*/\s*AgNO3")),
)
_CO2_PROPS = frozenset(
    {
        "Log10BindingConstant",
        "BindingConstant",
        "CaptureCapacity",
        "FaradaicEfficiency",
        "EnergyConsumption",
        "RateConstant",
    }
)
_THEORY = re.compile(r"theoretical|simulat|predicted|\bDFT\b", re.IGNORECASE)
_LABEL = re.compile(
    r"(?:state|states|step|steps|stage|figure|fig\.?|table|scheme|eq\.?|equation|ref\.?|entry|cycle)\s*$|\[\s*$",
    re.IGNORECASE,
)
_OXY = re.compile(r"oxygen|\bO\s?2\b|\b(?<!direct )air\b(?!\s*capture)", re.IGNORECASE)
_CITED = re.compile(
    r"^\s*(?:[A-Za-z\u03bc\u00b5\u00b0/\u22c5\u00b7%\s\-\u2212\d]{0,14})?\[\s*\d+(?:\s*[,\u2013-]\s*\d+)*\s*\]"
)
_COMPUTED = re.compile(r"calculat|comput|simulat|theoretical|predict|\bDFT\b|ab initio|modell?ed", re.IGNORECASE)
_BAD_OXY = re.compile(r"degrad|unstable|sensitiv|decompos|deactivat|oxidi[sz]|irreversibl|loss of", re.IGNORECASE)
_RANGE_FROM = re.compile(
    r"range[sd]?\s+(?:from|between)\s+([-\u2212\d.]+)\s+(?:to|and)\s+([-\u2212\d.]+)|ranging\s+from\s+([-\u2212\d.]+)\s+to\s+([-\u2212\d.]+)",
    re.IGNORECASE,
)
_RANGE = re.compile(r"between\s+([-\u2212\d.]+)\s+and\s+([-\u2212\d.]+)", re.IGNORECASE)
_CAPTURE_EFF = re.compile(r"capture efficiency|capture rate|removal efficiency|energy efficiency", re.IGNORECASE)
_FARADAIC = re.compile(r"farad|coulomb", re.IGNORECASE)
_ACTIVATION = re.compile(r"\u0394G\u2021|G\u2021|activation|barrier|\u2021", re.IGNORECASE)
_ENERGY_PROPS = frozenset({"BindingEnergy", "EnergyConsumption"})
_OTHER_COUPLE = re.compile(r"O\s?2\s?/\s?O\s?2|superoxide", re.IGNORECASE)


def _refs(compound: str, condition: str, where: str, compounds: set[str], conditions: set[str]) -> list[Problem]:
    out: list[Problem] = []
    if compound not in compounds:
        out.append(DanglingReference(where=where, key=compound))
    if condition not in conditions:
        out.append(DanglingReference(where=where, key=condition))
    return out


def _check_measurement(
    m: MeasurementRec, vocab: Vocabulary, where: str, compounds: set[str], conditions: set[str]
) -> list[Problem]:
    out = _refs(m.compound, m.condition, where, compounds, conditions)
    if m.basis == "Experiment" and any((m.functional, m.basis_set, m.solvation_model, m.dispersion, m.code)):
        out.append(ComputationSignatureOnExperiment(where=where))
    for field in ("functional", "basis_set", "solvation_model", "dispersion", "code"):
        value = getattr(m, field)
        if value and value != "NotReported" and value.casefold() not in m.quote.casefold():
            out.append(SignatureNotInQuote(where=where, field=field))
    out += _in(vocab, "Property", m.property, where) + _in(vocab, "Unit", m.unit, where)
    out += _in(vocab, "Basis", m.basis, where) + _in(vocab, "Method", m.method, where)
    prop = Term(m.property)
    allowed = vocab.allowed_units.get(prop, frozenset())
    if vocab.allows("Property", m.property) and Term(m.unit) not in allowed:
        out.append(UnitNotAllowed(where=where, prop=m.property, unit=m.unit, allowed=tuple(sorted(allowed))))
    out += _check_printed_unit(m, where)
    out += _check_scale_and_range(m, where)
    if m.property == "FaradaicEfficiency" and _CAPTURE_EFF.search(m.quote) and not _FARADAIC.search(m.quote):
        out.append(OtherQuantity(where=where, prop=m.property, word="capture efficiency"))
    if m.property == "BindingEnergy" and (word := _ACTIVATION.search(m.quote)):
        out.append(OtherQuantity(where=where, prop=m.property, word=word.group(0)))
    if prop in vocab.needs_couple and _OTHER_COUPLE.search(m.quote):
        out.append(OtherSpeciesPotential(where=where))
    if prop in vocab.needs_couple:
        if m.redox_couple is None:
            out.append(RedoxCoupleMissing(where=where))
        else:
            out += _in(vocab, "RedoxCouple", m.redox_couple, where)
    if (
        vocab.allows("Method", m.method)
        and vocab.allows("Basis", m.basis)
        and Term(m.basis) not in vocab.method_basis.get(Term(m.method), frozenset())
    ):
        out.append(MethodBasisMismatch(where=where, method=m.method, basis=m.basis))
    return out


def _refs_named(text: str) -> set[str]:
    return {name for name, pattern in _REFS if pattern.search(text)}


def _check_context(m: MeasurementRec, context: str, cond: ConditionRec | None, where: str) -> list[Problem]:
    out: list[Problem] = []
    if m.property == "BindingEnergy" and (word := _ACTIVATION.search(context)):
        out.append(OtherQuantity(where=where, prop=m.property, word=word.group(0)))
    if m.property in {"HalfWavePotential", "ReductionPotential"} and _OTHER_COUPLE.search(context):
        out.append(OtherSpeciesPotential(where=where))
    if any(_CITED.search(tail) for tail in after_value(m.quote, m.value, 28)):
        out.append(CitedValue(where=where, value=m.value))
    heads = before_value(m.quote, m.value)
    if heads and all(_LABEL.search(h) for h in heads):
        out.append(UnrelatedNumber(where=where, value=m.value))
    out += _check_provenance(m, context, where)
    if cond is not None:
        out += _check_condition_fit(m, cond, where)
    return out


def _check_provenance(m: MeasurementRec, context: str, where: str) -> list[Problem]:
    if m.basis == "Computation" and m.method not in {"DFT", "MolecularDynamics"} and not _COMPUTED.search(context):
        return [ComputationWithoutEvidence(where=where)]
    if m.basis == "Experiment":
        for head in before_value(context, m.value, 45):
            clause = re.split(r"[.;]\s|\bbut\b|\bwhile\b|\bwhereas\b", head)[-1]
            if word := _THEORY.search(clause):
                return [ProvenanceMismatch(where=where, word=word.group(0))]
    return []


def _check_condition_fit(m: MeasurementRec, cond: ConditionRec, where: str) -> list[Problem]:
    out: list[Problem] = []
    printed = _refs_named(m.quote)
    if printed and cond.reference_electrode not in printed and cond.reference_electrode != "NotReported":
        out.append(ReferenceContradicts(where=where, saved=cond.reference_electrode, printed=min(printed)))
    if m.property in _CO2_PROPS and cond.atmosphere == "Inert":
        out.append(AtmosphereContradicts(where=where, atmosphere="Inert", what=f"{m.property} (needs CO2)"))
    return out


def _check_evidence(o: ObservationRec, cond: ConditionRec | None, where: str) -> list[Problem]:
    out: list[Problem] = []
    quote = o.quote
    if cond is not None and cond.atmosphere == "Inert":
        out.append(AtmosphereContradicts(where=where, atmosphere="Inert", what=f"the observation {o.kind}"))
    match o.outcome:
        case "OxygenStable" | "OxygenUnstable" | "OxygenImproved":
            if not _OXY.search(quote):
                out.append(EvidenceMissing(where=where, outcome=o.outcome, why="no mention of oxygen or air"))
            if o.outcome == "OxygenStable" and _BAD_OXY.search(quote):
                out.append(EvidenceMissing(where=where, outcome=o.outcome, why="the quote describes degradation"))
        case "Bicarbonate":
            if not re.search(r"(?<!bis)bicarbonate|HCO\s?3", quote, re.IGNORECASE):
                out.append(EvidenceMissing(where=where, outcome=o.outcome, why="the quote does not say bicarbonate"))
        case "Carbonate":
            if not re.search(r"carbonate", quote, re.IGNORECASE):
                out.append(EvidenceMissing(where=where, outcome=o.outcome, why="the quote does not say carbonate"))
        case _:
            pass
    return out


def _check_scale_and_range(m: MeasurementRec, where: str) -> list[Problem]:
    out: list[Problem] = []
    for mantissa, full in powers_in(m.quote):
        if abs(mantissa - m.value) < 1e-9 and abs(full - m.value) > 1e-9:
            out.append(ScaleNotApplied(where=where, value=m.value))
    if any(_BOUND.search(head) for head in before_value(m.quote, m.value)) and not any(
        not _BOUND.search(head) for head in before_value(m.quote, m.value)
    ):
        out.append(BoundNotValue(where=where, value=m.value))
    for a, b, c, d in _RANGE_FROM.findall(m.quote):
        ends = [
            float(x.replace("\u2212", "-")) for x in (a, b, c, d) if re.fullmatch(r"[-\u2212]?\d+(?:\.\d+)?", x or "")
        ]
        if any(abs(e - m.value) < 1e-9 for e in ends):
            out.append(RangeBound(where=where, value=m.value))
    for first, second in _RANGE.findall(m.quote):
        ends = [float(x.replace("\u2212", "-")) for x in (first, second) if re.fullmatch(r"[-\u2212]?\d+(?:\.\d+)?", x)]
        if any(abs(e - m.value) < 1e-9 for e in ends):
            out.append(RangeBound(where=where, value=m.value))
    return out


def _check_printed_unit(m: MeasurementRec, where: str) -> list[Problem]:
    seen: list[tuple[str, bool]] = []
    for tail in after_value(m.quote, m.value):
        for label, pattern, allowed in _PRINTED_UNITS:
            if pattern.search(tail):
                seen.append((label, m.unit in allowed))
                break
    if not seen or any(ok for _, ok in seen):
        return []
    return [UnitNotInQuote(where=where, saved=m.unit, printed=seen[0][0])]


def _check_observation(
    o: ObservationRec, vocab: Vocabulary, where: str, compounds: set[str], conditions: set[str]
) -> list[Problem]:
    out = _refs(o.compound, o.condition, where, compounds, conditions)
    out += _in(vocab, "ObservationKind", o.kind, where) + _in(vocab, "Outcome", o.outcome, where)
    if (
        vocab.allows("ObservationKind", o.kind)
        and vocab.allows("Outcome", o.outcome)
        and Term(o.kind) not in vocab.outcome_kind.get(Term(o.outcome), frozenset())
    ):
        out.append(OutcomeKindMismatch(where=where, outcome=o.outcome, kind=o.kind))
    return out
