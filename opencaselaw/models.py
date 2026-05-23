"""Data models for stable OpenCaseLaw response shapes."""

from dataclasses import dataclass, field
from typing import Any


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    text = str(value)
    if not text:
        raise ValueError(f"Missing required field: {key}")
    return text


@dataclass(frozen=True)
class DecisionSummary:
    """A compact decision returned by the search endpoint."""

    decision_id: str
    court: str | None = None
    decision_date: str | None = None
    language: str | None = None
    title: str | None = None
    regeste: str | None = None
    citation_string_de: str | None = None
    citation_string_fr: str | None = None
    citation_string_it: str | None = None
    canonical_url: str | None = None
    rule_statement: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "DecisionSummary":
        """Create a summary from an OpenCaseLaw search result object."""
        return cls(
            decision_id=_required_string(data, "decision_id"),
            court=_string_or_none(data.get("court")),
            decision_date=_string_or_none(data.get("decision_date")),
            language=_string_or_none(data.get("language")),
            title=_string_or_none(data.get("title")),
            regeste=_string_or_none(data.get("regeste")),
            citation_string_de=_string_or_none(data.get("citation_string_de")),
            citation_string_fr=_string_or_none(data.get("citation_string_fr")),
            citation_string_it=_string_or_none(data.get("citation_string_it")),
            canonical_url=_string_or_none(data.get("canonical_url")),
            rule_statement=_string_or_none(data.get("rule_statement")),
            raw=data,
        )


@dataclass(frozen=True)
class DecisionSearchResult:
    """Paginated decision search response."""

    total: int
    results: list[DecisionSummary]
    limit: int
    offset: int
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "DecisionSearchResult":
        """Create a search result from API JSON."""
        raw_results = data.get("results", [])
        results = [
            DecisionSummary.from_json(item)
            for item in raw_results
            if isinstance(item, dict)
        ]
        return cls(
            total=int(data.get("total", len(results))),
            results=results,
            limit=int(data.get("limit", len(results))),
            offset=int(data.get("offset", 0)),
            raw=data,
        )


@dataclass(frozen=True)
class Decision:
    """A full decision response."""

    decision_id: str
    docket_number: str | None = None
    court: str | None = None
    decision_date: str | None = None
    language: str | None = None
    title: str | None = None
    regeste: str | None = None
    full_text: str | None = None
    citation_string_de: str | None = None
    citation_string_fr: str | None = None
    citation_string_it: str | None = None
    canonical_url: str | None = None
    rule_statement: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Decision":
        """Create a decision from API JSON."""
        return cls(
            decision_id=_required_string(data, "decision_id"),
            docket_number=_string_or_none(data.get("docket_number")),
            court=_string_or_none(data.get("court")),
            decision_date=_string_or_none(data.get("decision_date")),
            language=_string_or_none(data.get("language")),
            title=_string_or_none(data.get("title")),
            regeste=_string_or_none(data.get("regeste")),
            full_text=_string_or_none(data.get("full_text")),
            citation_string_de=_string_or_none(data.get("citation_string_de")),
            citation_string_fr=_string_or_none(data.get("citation_string_fr")),
            citation_string_it=_string_or_none(data.get("citation_string_it")),
            canonical_url=_string_or_none(data.get("canonical_url")),
            rule_statement=_string_or_none(data.get("rule_statement")),
            raw=data,
        )


@dataclass(frozen=True)
class LawArticle:
    """A statute article returned by a law lookup."""

    article_num: str
    heading: str | None
    text: str
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "LawArticle":
        """Create a law article from API JSON."""
        return cls(
            article_num=_required_string(data, "article_num"),
            heading=_string_or_none(data.get("heading")),
            text=_required_string(data, "text"),
            raw=data,
        )


@dataclass(frozen=True)
class Law:
    """A law lookup response."""

    sr_number: str | None
    abbreviation: str | None
    title: str | None
    consolidation_date: str | None
    language: str | None
    articles: list[LawArticle]
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Law":
        """Create a law response from API JSON."""
        raw_articles = data.get("articles", [])
        articles = [
            LawArticle.from_json(item)
            for item in raw_articles
            if isinstance(item, dict)
        ]
        return cls(
            sr_number=_string_or_none(data.get("sr_number")),
            abbreviation=_string_or_none(data.get("abbreviation")),
            title=_string_or_none(data.get("title")),
            consolidation_date=_string_or_none(data.get("consolidation_date")),
            language=_string_or_none(data.get("language")),
            articles=articles,
            raw=data,
        )


@dataclass(frozen=True)
class Court:
    """A court listing item."""

    court: str
    name: str | None = None
    count: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Court":
        """Create a court from API JSON."""
        count = data.get("count", data.get("decision_count"))
        court = data.get("court", data.get("court_code"))
        return cls(
            court=_required_string({"court": court}, "court"),
            name=_string_or_none(data.get("name")),
            count=int(count) if count is not None else None,
            raw=data,
        )


@dataclass(frozen=True)
class Citation:
    """A canonical citation response."""

    decision_id: str | None = None
    citation_string_de: str | None = None
    citation_string_fr: str | None = None
    citation_string_it: str | None = None
    canonical_url: str | None = None
    rule_statement: str | None = None
    exists: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Citation":
        """Create a citation from API JSON."""
        return cls(
            decision_id=_string_or_none(data.get("decision_id")),
            citation_string_de=_string_or_none(data.get("citation_string_de")),
            citation_string_fr=_string_or_none(data.get("citation_string_fr")),
            citation_string_it=_string_or_none(data.get("citation_string_it")),
            canonical_url=_string_or_none(data.get("canonical_url")),
            rule_statement=_string_or_none(data.get("rule_statement")),
            exists=data.get("exists") if isinstance(data.get("exists"), bool) else None,
            raw=data,
        )
