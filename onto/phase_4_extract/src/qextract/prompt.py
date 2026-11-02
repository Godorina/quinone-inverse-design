"""Builds the instruction for the model from the ontology vocabulary, so the prompt cannot drift from the checker."""

from .vocab import Vocabulary

_SCHEMES = (
    ("Skeleton", "compounds[].skeleton"),
    ("Form", "compounds[].form"),
    ("SubstituentClass", "compounds[].substituent_classes[]"),
    ("Solvent", "conditions[].solvent"),
    ("ReferenceElectrode", "conditions[].reference_electrode"),
    ("Atmosphere", "conditions[].atmosphere"),
    ("Property", "measurements[].property"),
    ("Unit", "measurements[].unit"),
    ("Basis", "measurements[].basis"),
    ("Method", "measurements[].method"),
    ("RedoxCouple", "measurements[].redox_couple"),
    ("ObservationKind", "observations[].kind"),
    ("Outcome", "observations[].outcome"),
)

_RULES = """You copy results about quinone-based electrochemical CO2 capture out of ONE paper into JSON.
You never estimate, convert, or compute a value the paper does not print. Every item carries a `quote`: ONE sentence,
table row or fragment copied character for character from the paper text, on a single page, that prints what the item
says. A number must appear in its own quote. If the paper does not state a detail, use NotReported (never guess).

Items:
- compounds: each quinone (or quinone material) the paper uses as a CO2 carrier or compares. `key` is a short id
  you choose (letters, digits, underscore). `name` must appear in the text. `quote` names or describes the compound.
  Use the closest skeleton; use NotReported when the paper does not say.
  Unsubstituted parent = substituent class Unsubstituted.
- conditions: each distinct medium in which values were obtained: solvent, reference electrode of the potentials,
  atmosphere. `quote` must show at least one of them (for example the electrolyte or the reference electrode sentence).
- Use one condition per distinct medium: values at different pH, salt, additive (for example ethanol 0.66 M) or solvent
  need different conditions with `ph`, `electrolyte_text` or `additive_text` filled from the paper. Never put two
  different values of the same property for one compound in one condition.
- Condition key "unspecified" (no entry needed) is for a value
  whose medium the paper does not give, such as a DFT result.
- Tables: quote the printed row or line that holds the value exactly as the text prints it, even when that line also
  holds values of other compounds (tables are often printed column by column). Never rebuild a row as
  "compound value"; the saved value only has to be one of the numbers in your quote.
  A short row is fine if it is unique.
- measurements: one printed number each (potential, binding constant, energy, capacity, efficiency, rate constant),
  with `compound` and `condition` keys. `unit` must be allowed for the property.
  Potentials need `redox_couple`.
  basis is Experiment for measured values and Computation for DFT or simulation values.
  For Computation only, copy functional, basis_set, solvation_model, dispersion and code exactly from the calculation-method section when printed; otherwise omit them (NotReported is not a guessed value).
- observations: how CO2 is bound (BindingMode) or whether the compound survives oxygen (OxygenStability).
Units: copy the unit that is printed right after the number. A concentration "2.2 M" is not a capacity per quinone,
a first-order "s-1" is not a second-order "M-1 s-1", and an activation barrier (delta G double dagger) is not a binding
energy. If no allowed unit fits, leave the item out.
Quotes: never abbreviate, reorder or "clean up" a quote; copy a shorter exact fragment instead (at least 8 characters).
Do not record generic ranges or typical values for a class of compounds; record values of named compounds.
Do not record potentials of other species (for example the O2/O2 radical anion or the reference couple).
Only include what the paper reports about the quinone carriers of its own work, not values cited from other papers.
Return one JSON object:
{"compounds": [], "conditions": [], "measurements": [], "observations": [], "not_reported": []}.
`not_reported` lists in plain words what could not be found
(for example "reference electrode of the potentials").
Reply with the JSON object only."""


def build_system(vocab: Vocabulary) -> str:
    """Return the instruction text with the allowed values of every controlled field listed from the vocabulary."""
    lines = [_RULES, "", "Allowed values (exact spelling):"]
    for scheme, field in _SCHEMES:
        terms = sorted(vocab.schemes.get(scheme, frozenset()))
        lines.append(f"- {field}: {', '.join(terms)}")
    lines += ["", "Allowed units per property:"]
    for prop in sorted(vocab.allowed_units):
        lines.append(f"- {prop}: {', '.join(sorted(vocab.allowed_units[prop]))}")
    lines.append(f"Properties that need redox_couple: {', '.join(sorted(vocab.needs_couple))}")
    return "\n".join(lines)


def user_message(title: str, text: str, *, abstract_only: bool) -> str:
    """Return the paper as the user turn."""
    note = (
        "This is only the abstract; there are no page numbers. Skip anything the abstract does not print.\n"
        if abstract_only
        else "The text has `===== PAGE n =====` lines; each quote must lie within one page.\n"
    )
    return f"Paper: {title}\n{note}\n{text}"


def repair_message(problems: list[str]) -> str:
    """Return the second turn: the checker's refusals, to be fixed in a complete new JSON object."""
    listed = "\n".join(f"- {p}" for p in problems[:40])
    return (
        "Some items were refused and are not saved:\n"
        f"{listed}\n"
        "Return the COMPLETE JSON object again with those items fixed or removed. Keep every item that was fine."
    )
