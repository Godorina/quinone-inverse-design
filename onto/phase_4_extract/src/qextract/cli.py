"""Command line: run extraction over the master list, resumable, one JSON file per paper."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, ClassVar

import typer
from pydantic import BaseModel, ConfigDict, TypeAdapter

from .llm import DEFAULT_URL, LlmUnavailableError, Message, chat
from .pipeline import PaperInput, extract, render
from .prompt import build_system
from .text import Page, split_pages
from .vocab import load

app = typer.Typer(no_args_is_help=True)


class MasterEntry(BaseModel):
    """The fields of `master.json` this tool reads."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")
    id: str
    title: str
    label: str
    fulltext: str
    abstract: str = ""
    text_file: str | None = None


def _paper(entry: MasterEntry, root: Path) -> PaperInput | None:
    if entry.fulltext == "fulltext" and entry.text_file:
        return PaperInput(
            entry.id,
            entry.title,
            split_pages((root / entry.text_file).read_text(encoding="utf-8")),
            abstract_only=False,
        )
    if entry.abstract.strip():
        return PaperInput(entry.id, entry.title, (Page(1, f"{entry.title}\n\n{entry.abstract}"),), abstract_only=True)
    return None


@app.command()
def run(
    ids: Annotated[list[str] | None, typer.Argument(help="master ids such as m001; empty = every target")] = None,
    master: Annotated[Path, typer.Option(help="master.json")] = Path("../4_corpus/master.json"),
    vocab_ttl: Annotated[Path, typer.Option(help="quinone-vocab.ttl")] = Path("tests/fixtures/quinone-vocab.ttl"),
    out: Annotated[Path, typer.Option(help="folder for records")] = Path("records"),
    url: Annotated[str, typer.Option(help="llama-server base url")] = DEFAULT_URL,
    retries: Annotated[int, typer.Option()] = 3,
    abstract_only: Annotated[bool, typer.Option(help="only the abstract-only papers")] = False,
    redo: Annotated[bool, typer.Option(help="re-extract papers that already have a record")] = False,
) -> None:
    """Extract the selected papers; a paper with a record is skipped unless --redo."""
    entries = TypeAdapter(list[MasterEntry]).validate_json(master.read_text(encoding="utf-8"))
    wanted = [e for e in entries if e.label == "on_topic" and (not ids or e.id in ids)]
    root = master.parent.parent
    vocab = load(vocab_ttl)
    system = build_system(vocab)
    out.mkdir(parents=True, exist_ok=True)

    def chat_fn(messages: Sequence[Message]) -> str:
        return chat(url, messages)

    for entry in wanted:
        dest = out / f"{entry.id}.json"
        paper = _paper(entry, root)
        if paper is None or (paper.abstract_only != abstract_only and not ids):
            continue
        if dest.exists() and not redo:
            continue
        try:
            outcome = extract(paper, vocab, system, chat_fn, retries=retries)
        except LlmUnavailableError as e:
            typer.echo(f"{entry.id}: stopped: {e}")
            raise typer.Exit(code=2) from e
        dest.write_text(render(paper, outcome), encoding="utf-8")
        c = outcome.checked
        typer.echo(
            f"{entry.id} kept m={len(c.measurements)} o={len(c.observations)} "
            f"c={len(c.compounds)} k={len(c.conditions)} "
            f"dropped={len(c.dropped)} attempts={len(outcome.attempts)}"
        )


@app.command()
def tally(out: Annotated[Path, typer.Option()] = Path("records")) -> None:
    """Count kept and dropped items over all saved records."""
    total = {"measurements": 0, "observations": 0, "compounds": 0, "conditions": 0, "dropped": 0}
    files = sorted(out.glob("m*.json"))
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        for k in total:
            total[k] += len(doc[k])
    typer.echo(f"{len(files)} records: {total}")


if __name__ == "__main__":
    app()
