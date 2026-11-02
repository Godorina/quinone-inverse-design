"""The shape the model must return. Data from the model crosses a trust boundary, so it is parsed here."""

from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Key = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,39}$")]
Quote = Annotated[str, StringConstraints(min_length=8, max_length=700)]
MAX_QUOTE = 700


class _Frozen(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class CompoundRec(_Frozen):
    """A quinone compound or material the paper uses as a CO2 carrier."""

    key: Key
    name: str = Field(min_length=2, max_length=160)
    skeleton: str
    form: str
    substituent_classes: tuple[str, ...] = Field(min_length=1)
    substituent_text: str | None = None
    quote: Quote


class ConditionRec(_Frozen):
    """The medium and setting in which values were obtained."""

    key: Key
    solvent: str
    reference_electrode: str
    atmosphere: str
    electrolyte_text: str | None = None
    additive_text: str | None = None
    ph: float | None = None
    temperature_k: float | None = None
    quote: Quote


class MeasurementRec(_Frozen):
    """One printed number about one compound under one condition."""

    compound: Key
    condition: Key
    property: str
    value: float
    unit: str
    basis: str
    method: str
    redox_couple: str | None = None
    functional: str | None = None
    basis_set: str | None = None
    solvation_model: str | None = None
    dispersion: str | None = None
    code: str | None = None
    quote: Quote


class ObservationRec(_Frozen):
    """A categorical statement: binding mode or oxygen stability."""

    compound: Key
    condition: Key
    kind: str
    outcome: str
    quote: Quote


class PaperRecord(_Frozen):
    """Everything extracted from one paper."""

    compounds: tuple[CompoundRec, ...] = ()
    conditions: tuple[ConditionRec, ...] = ()
    measurements: tuple[MeasurementRec, ...] = ()
    observations: tuple[ObservationRec, ...] = ()
    not_reported: tuple[str, ...] = ()
