"""Controlled vocabulary read from the ontology's quinone-vocab.ttl: one place, no copy."""

from dataclasses import dataclass
from pathlib import Path
from typing import Final, NewType

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, SKOS

QN: Final = Namespace("https://w3id.org/quinone#")
Term = NewType("Term", str)


@dataclass(frozen=True, slots=True)
class Vocabulary:
    """Allowed terms per scheme plus the cross-term rules the SHACL files also check."""

    schemes: dict[str, frozenset[Term]]
    allowed_units: dict[Term, frozenset[Term]]
    needs_couple: frozenset[Term]
    method_basis: dict[Term, frozenset[Term]]
    outcome_kind: dict[Term, frozenset[Term]]
    definitions: dict[Term, str]

    def allows(self, scheme: str, term: str) -> bool:
        """True when `term` is a concept of `scheme`."""
        return Term(term) in self.schemes.get(scheme, frozenset())


def _local(uri: URIRef) -> Term:
    return Term(str(uri).removeprefix(str(QN)))


def load(ttl: Path) -> Vocabulary:
    """Parse the vocabulary file; raises FileNotFoundError or a parser error if it is unusable."""
    graph = Graph()
    graph.parse(ttl)
    schemes: dict[str, set[Term]] = {}
    for concept in graph.subjects(RDF.type, SKOS.Concept):
        if not isinstance(concept, URIRef):
            continue
        for scheme in graph.objects(concept, SKOS.inScheme):
            if isinstance(scheme, URIRef):
                schemes.setdefault(_local(scheme).removesuffix("Scheme"), set()).add(_local(concept))

    def related(prop: str) -> dict[Term, frozenset[Term]]:
        out: dict[Term, set[Term]] = {}
        for s, o in graph.subject_objects(QN[prop]):
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                out.setdefault(_local(s), set()).add(_local(o))
        return {k: frozenset(v) for k, v in out.items()}

    needs = frozenset(
        _local(s)
        for s, o in graph.subject_objects(QN["requiresRedoxCouple"])
        if isinstance(s, URIRef) and str(o) == "true"
    )
    definitions = {
        _local(c): str(d)
        for c, d in graph.subject_objects(SKOS.definition)
        if isinstance(c, URIRef) and getattr(d, "language", None) == "en"
    }
    return Vocabulary(
        definitions=definitions,
        schemes={k: frozenset(v) for k, v in schemes.items()},
        allowed_units=related("allowedUnit"),
        needs_couple=needs,
        method_basis=related("appliesToBasis"),
        outcome_kind=related("forKind"),
    )
