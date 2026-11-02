"""Extract one paper: ask, check, send the refusals back, keep the best attempt."""

import dataclasses
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, JsonValue, TypeAdapter, ValidationError

from .checker import Checked, DanglingReference, Dropped, MalformedItem, Problem, check, describe
from .llm import Message
from .prompt import repair_message, user_message
from .record import CompoundRec, ConditionRec, MeasurementRec, ObservationRec, PaperRecord
from .text import Page
from .vocab import Vocabulary

type ChatFn = Callable[[Sequence[Message]], str]

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


@dataclass(frozen=True, slots=True)
class PaperInput:
    """What the model reads: the paper's pages, or its abstract as one pseudo page."""

    paper_id: str
    title: str
    pages: tuple[Page, ...]
    abstract_only: bool


@dataclass(frozen=True, slots=True)
class Attempt:
    """One round trip with the model."""

    number: int
    parse_errors: tuple[str, ...]
    kept: int
    dropped: int


@dataclass(frozen=True, slots=True)
class Outcome:
    """The best attempt's checked record, the model's not_reported notes, and the attempt log."""

    checked: Checked
    not_reported: tuple[str, ...]
    attempts: tuple[Attempt, ...]


def _kept(c: Checked) -> int:
    return len(c.compounds) + len(c.conditions) + len(c.measurements) + len(c.observations)


def _lines(checked: Checked) -> list[str]:
    problems: list[Problem] = [p for d in checked.dropped for p in d.problems]
    roots = [describe(p) for p in problems if not isinstance(p, DanglingReference)]
    keys: dict[str, int] = {}
    for p in problems:
        if isinstance(p, DanglingReference):
            keys[p.key] = keys.get(p.key, 0) + 1
    effects = [
        f"'{k}' was refused or is missing, so {n} result(s) that use it were refused too; fix '{k}' first"
        for k, n in keys.items()
    ]
    return [*effects, *roots]


_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_ITEM_MODELS: dict[str, type[BaseModel]] = {
    "compounds": CompoundRec,
    "conditions": ConditionRec,
    "measurements": MeasurementRec,
    "observations": ObservationRec,
}


def _clip(value: JsonValue, limit: int = 300) -> JsonValue:
    if isinstance(value, str):
        return value if len(value) <= limit else f"{value[:limit]}... ({len(value)} characters)"
    if isinstance(value, list):
        return [_clip(v, limit) for v in value]
    if isinstance(value, dict):
        return {k: _clip(v, limit) for k, v in value.items()}
    return value


def _errors(e: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()[:4])


@dataclass(frozen=True, slots=True)
class Parsed:
    """A reply that held a JSON object: the items that have the right shape and those that do not."""

    record: PaperRecord
    malformed: tuple[Dropped, ...]


@dataclass(frozen=True, slots=True)
class Unreadable:
    """A reply that is not one JSON object; nothing in it can be used."""

    reasons: tuple[str, ...]


type ParseResult = Parsed | Unreadable


def _parse(reply: str) -> ParseResult:
    try:
        raw = _JSON.validate_json(_FENCE.sub("", reply.strip()))
    except ValidationError as e:
        return Unreadable((f"not valid JSON: {e.errors()[0]['msg']}",))
    if not isinstance(raw, dict):
        return Unreadable(("the reply must be one JSON object",))
    good: dict[str, list[BaseModel]] = {name: [] for name in _ITEM_MODELS}
    bad: list[Dropped] = []
    for name, model in _ITEM_MODELS.items():
        items = raw.get(name, [])
        if not isinstance(items, list):
            return Unreadable((f"{name} must be a list",))
        for i, item in enumerate(items):
            try:
                good[name].append(model.model_validate(item))
            except ValidationError as e:
                problem = MalformedItem(where=f"{name}[{i}]", message=_errors(e))
                bad.append(
                    Dropped(
                        kind=name.removesuffix("s"),
                        raw=json.dumps(_clip(item), ensure_ascii=False),
                        problems=(problem,),
                    )
                )
    notes = raw.get("not_reported", [])
    record = PaperRecord(
        compounds=tuple(i for i in good["compounds"] if isinstance(i, CompoundRec)),
        conditions=tuple(i for i in good["conditions"] if isinstance(i, ConditionRec)),
        measurements=tuple(i for i in good["measurements"] if isinstance(i, MeasurementRec)),
        observations=tuple(i for i in good["observations"] if isinstance(i, ObservationRec)),
        not_reported=tuple(str(n) for n in notes) if isinstance(notes, list) else (),
    )
    return Parsed(record, tuple(bad))


def extract(paper: PaperInput, vocab: Vocabulary, system: str, chat_fn: ChatFn, *, retries: int = 3) -> Outcome:
    """Ask for a record, check it, send refusals back up to `retries` times; return the attempt that kept the most."""
    text = "".join(f"\n===== PAGE {p.number} =====\n{p.text}" for p in paper.pages)
    messages = [
        Message("system", system),
        Message("user", user_message(paper.title, text, abstract_only=paper.abstract_only)),
    ]
    best: tuple[Checked, tuple[str, ...]] | None = None
    attempts: list[Attempt] = []
    for n in range(1, retries + 2):
        reply = chat_fn(messages)
        match _parse(reply):
            case Unreadable(reasons=reasons):
                attempts.append(Attempt(n, reasons, 0, 0))
                messages += [
                    Message("assistant", reply),
                    Message("user", repair_message([f"JSON format: {e}" for e in reasons])),
                ]
                continue
            case Parsed(record=record, malformed=malformed):
                checked = check(record, paper.pages, vocab, abstract=paper.abstract_only)
                checked = dataclasses.replace(checked, dropped=(*malformed, *checked.dropped))
        attempts.append(Attempt(n, (), _kept(checked), len(checked.dropped)))
        if best is None or _kept(checked) > _kept(best[0]):
            best = (checked, record.not_reported)
        if not checked.dropped:
            break
        messages += [Message("assistant", reply), Message("user", repair_message(_lines(checked)))]
    if best is None:
        empty = Checked((), (), (), (), ())
        return Outcome(empty, (), tuple(attempts))
    return Outcome(best[0], best[1], tuple(attempts))


def render(paper: PaperInput, outcome: Outcome) -> str:
    """The saved record as JSON text: kept items with their pages, dropped items with reasons, the attempt log."""
    c = outcome.checked

    def items(located: Sequence[object]) -> list[JsonValue]:
        out: list[JsonValue] = []
        for loc in located:
            item = getattr(loc, "item")  # noqa: B009
            out.append({**json.loads(item.model_dump_json()), "page": getattr(loc, "page")})  # noqa: B009
        return out

    doc: dict[str, JsonValue] = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "evidence_source": "Abstract" if paper.abstract_only else "FullText",
        "compounds": items(c.compounds),
        "conditions": items(c.conditions),
        "measurements": items(c.measurements),
        "observations": items(c.observations),
        "not_reported": list(outcome.not_reported),
        "dropped": [
            {"kind": d.kind, "raw": json.loads(d.raw), "reasons": [describe(p) for p in d.problems]} for d in c.dropped
        ],
        "attempts": [
            {"n": a.number, "parse_errors": list(a.parse_errors), "kept": a.kept, "dropped": a.dropped}
            for a in outcome.attempts
        ],
        "review_status": "machine_extracted",
    }
    return json.dumps(doc, ensure_ascii=False, indent=1)
