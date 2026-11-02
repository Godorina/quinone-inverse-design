"""Paper text with page markers and the quote matcher that decides whether a quote is verbatim."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Final

_PAGE_MARK: Final = re.compile(r"^===== PAGE (\d+) =====$", re.MULTILINE)
_DASH: Final = re.compile("[\u2010\u2011\u2012\u2013\u2014\u2212\u2012]")
_QUOTE_MARKS: Final = re.compile("[\u2032\u2019\u2018\u00b4`]")


@dataclass(frozen=True, slots=True)
class Page:
    """One page of a paper: its 1-based number and its raw text."""

    number: int
    text: str


@dataclass(frozen=True, slots=True)
class QuoteFound:
    """The quote sits on a single page."""

    page: int


@dataclass(frozen=True, slots=True)
class QuoteMissing:
    """The quote is on no page; `closest` helps the model repair it."""

    closest: str


type QuoteMatch = QuoteFound | QuoteMissing


def split_pages(full_text: str) -> tuple[Page, ...]:
    """Cut a converted paper (see `===== PAGE n =====` lines) into pages."""
    marks = list(_PAGE_MARK.finditer(full_text))
    pages: list[Page] = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(full_text)
        pages.append(Page(number=int(mark.group(1)), text=full_text[mark.end() : end]))
    return tuple(pages)


_PRIVATE_LIGATURES: Final = {"\ue103": "fi", "\ue09d": "ft", "\ue104": "fl"}
_HYPHEN: Final = re.compile(r"(?<=[A-Za-z0-9\]\)])-(?=[A-Za-z\[\(])")


def normalize(text: str) -> str:
    """Lowercase and drop whitespace; unify dashes and primes; drop hyphens between letters, keep a minus sign.

    A hyphen at a line end may be typesetting or part of a name, so hyphens are ignored on both sides of a comparison.
    """
    unified = _QUOTE_MARKS.sub("'", _DASH.sub("-", unicodedata.normalize("NFKC", text))).replace("\u00ad", "")
    for private, letters in _PRIVATE_LIGATURES.items():
        unified = unified.replace(private, letters)
    return _HYPHEN.sub("", re.sub(r"\s+", "", unified)).lower()


SHORT_QUOTE: Final = 15


def find_quote(pages: tuple[Page, ...], quote: str) -> QuoteMatch:
    """Locate `quote` on exactly one page; a short quote (a table row) must also occur only once in the paper."""
    needle = normalize(quote)
    if len(needle) < 6:
        return QuoteMissing(closest="quote too short (needs at least 8 characters)")
    hits = [p.number for p in pages if needle in normalize(p.text)]
    if not hits:
        return QuoteMissing(closest=_closest(pages, needle))
    total = sum(normalize(p.text).count(needle) for p in pages)
    if len(needle) < SHORT_QUOTE and total > 1:
        return QuoteMissing(
            closest=f"this short quote appears more than once (pages {sorted(set(hits))}); "
            "quote a longer fragment that includes the row label or the sentence around it"
        )
    return QuoteFound(page=hits[0])


def _best_overlap(needle: str, hay: str) -> tuple[int, int]:
    """Return (start, length) of the longest prefix of `needle` found in `hay`, at least 12 characters."""
    best = (-1, 0)
    for size in range(min(len(needle), 60), 11, -1):
        at = hay.find(needle[:size])
        if at >= 0:
            best = (at, size)
            break
    return best


def _closest(pages: tuple[Page, ...], needle: str) -> str:
    found: tuple[int, int, int, str] | None = None
    for page in pages:
        hay = normalize(page.text)
        at, size = _best_overlap(needle, hay)
        if size and (found is None or size > found[2]):
            found = (page.number, at, size, hay)
    if found is None:
        return "no page contains the start of this quote; copy it exactly from the page text"
    number, at, size, hay = found
    same = size
    while same < len(needle) and at + same < len(hay) and needle[same] == hay[at + same]:
        same += 1
    return (
        f"page {number}: your quote matches up to '...{hay[max(at, at + same - 25) : at + same]}' "
        f"then the page has '{hay[at + same : at + same + 40]}' "
        f"but you wrote '{needle[same : same + 40]}' (spaces ignored)"
    )


_DECIMAL_COMMA: Final = re.compile(r"(?<=\d),(?=\d)")
_NUMBER: Final = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def context_of(pages: tuple[Page, ...], quote: str, width: int = 90) -> str:
    """Return the quote with `width` characters of its page on each side; just the quote when it cannot be placed."""
    needle = _locate_form(quote)
    for page in pages:
        hay = _locate_form(page.text)
        at = hay.find(needle)
        if needle and at >= 0:
            return hay[max(0, at - width) : at + len(needle) + width]
    return quote


def _locate_form(text: str) -> str:
    unified = unicodedata.normalize("NFKC", text)
    for private, letters in _PRIVATE_LIGATURES.items():
        unified = unified.replace(private, letters)
    return re.sub(r"\s+", " ", _QUOTE_MARKS.sub("'", _DASH.sub("-", unified))).strip().lower()


def before_value(text: str, value: float, width: int = 16) -> list[str]:
    """Return the `width` characters printed right before each occurrence of `value` in `text`."""
    cleaned = _DECIMAL_COMMA.sub(".", _DASH.sub("-", unicodedata.normalize("NFKC", text)))
    out: list[str] = []
    for m in _NUMBER.finditer(cleaned):
        try:
            same = abs(float(m.group(0)) - value) < 1e-9
        except ValueError:
            continue
        if same:
            out.append(cleaned[max(0, m.start() - width) : m.start()])
    return out


_POWER: Final = re.compile(r"([-+]?\d+(?:[.,]\d+)?)\s*[\u00d7x\u22c5\u00b7*]\s*10\s*(?:\^\s*)?([-+]?\d+)")


def after_value(text: str, value: float, width: int = 16) -> list[str]:
    """Return the `width` characters printed right after each occurrence of `value`, also as "a x 10n"."""
    cleaned = _DECIMAL_COMMA.sub(".", _DASH.sub("-", unicodedata.normalize("NFKC", text)))
    out: list[str] = []
    for m in _NUMBER.finditer(cleaned):
        try:
            same = abs(float(m.group(0)) - value) < 1e-9
        except ValueError:
            continue
        if same:
            out.append(cleaned[m.end() : m.end() + width])
    for m in _POWER.finditer(cleaned):
        mantissa = float(m.group(1))
        if abs(mantissa * 10 ** int(m.group(2)) - value) <= 1e-9 * max(1.0, abs(value)):
            out.append(cleaned[m.end() : m.end() + width])
    return out


def powers_in(text: str) -> tuple[tuple[float, float], ...]:
    """Return (mantissa, full value) for every "a x 10n" in `text`; a flattened superscript is the exponent."""
    cleaned = _DASH.sub("-", unicodedata.normalize("NFKC", text))
    out: list[tuple[float, float]] = []
    for m in _POWER.finditer(cleaned):
        try:
            out.append(
                (float(m.group(1).replace(",", ".")), float(m.group(1).replace(",", ".")) * 10 ** int(m.group(2)))
            )
        except (ValueError, OverflowError):
            continue
    return tuple(out)


def numbers_in(text: str) -> tuple[float, ...]:
    """Return all numbers printed in `text`; the dash family counts as a minus sign and "a x 10n" counts as a x 10^n."""
    cleaned = _DECIMAL_COMMA.sub(".", _DASH.sub("-", text))
    out: list[float] = []
    for m in _NUMBER.finditer(cleaned):
        try:
            out.append(float(m.group(0)))
        except ValueError:
            continue
    return (*out, *(full for _, full in powers_in(text)))


def contains(pages: tuple[Page, ...], phrase: str) -> bool:
    """True when `phrase` is on some page after normalization; no minimum length."""
    needle = normalize(phrase)
    return bool(needle) and any(needle in normalize(p.text) for p in pages)
