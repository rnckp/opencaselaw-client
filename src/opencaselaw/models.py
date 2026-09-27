"""Validated models for stable OpenCaseLaw response shapes."""

from typing import Annotated, Any, Self

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    StringConstraints,
    model_validator,
)

RequiredString = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
NonNegativeInt = Annotated[int, Field(ge=0, strict=True)]


class _ResponseModel(BaseModel):
    """Validate known fields while retaining the original response payload."""

    model_config = ConfigDict(frozen=True, extra="ignore", hide_input_in_errors=True)
    ignored_arguments: list[str] | None = None
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

    @model_validator(mode="wrap")
    @classmethod
    def _preserve_raw(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        result = handler(data)
        if isinstance(data, dict):
            # Keep the original mapping, including unknown fields, for nested models too.
            object.__setattr__(result, "raw", data.get("raw", data))
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Validate API JSON, preserving the complete input in ``raw``.

        Raises:
            pydantic.ValidationError: A known field has an invalid shape or value.
        """
        result = cls.model_validate(data)
        object.__setattr__(result, "raw", data)
        return result


class DecisionSummary(_ResponseModel):
    """A compact decision returned by the search endpoint."""

    decision_id: RequiredString
    docket_number: str | None = None
    canton: str | None = None
    publication_date: str | None = None
    date_is_estimated: bool | None = Field(default=None, strict=True)
    source_url: str | None = None
    pdf_url: str | None = None
    snippet: str | None = None
    pinpoint: dict[str, Any] | None = None
    citation_count: NonNegativeInt | None = None
    is_leading_case: bool | None = Field(default=None, strict=True)
    joined_dockets: list[str] | None = None
    canonical_decision_id: str | None = None
    is_canonical: bool | None = Field(default=None, strict=True)
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


class DecisionSearchResult(_ResponseModel):
    """Paginated decision search response."""

    total: NonNegativeInt = 0
    results: list[DecisionSummary] = Field(default_factory=list)
    limit: NonNegativeInt = 0
    offset: NonNegativeInt = 0
    total_is_lower_bound: bool | None = Field(default=None, strict=True)
    returned: NonNegativeInt | None = None
    has_more: bool | None = Field(default=None, strict=True)
    next_offset: NonNegativeInt | None = None
    result_set_id: str | None = None
    query_condensed: bool | None = Field(default=None, strict=True)
    condensed_terms: list[str] | None = None
    note: str | None = None
    degraded: bool | None = Field(default=None, strict=True)

    @model_validator(mode="before")
    @classmethod
    def _default_counts(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("results", []), list):
            count = len(data.get("results", []))
            return {"total": count, "limit": count, **data}
        return data


class Decision(DecisionSummary):
    """A full decision response."""

    full_text: str | None = None
    full_text_total_chars: NonNegativeInt | None = None
    full_text_returned_chars: NonNegativeInt | None = None
    full_text_truncated: bool | None = Field(default=None, strict=True)
    full_text_url: str | None = None
    recency_note: str | None = None


class LawArticle(_ResponseModel):
    """A statute article returned by a law lookup."""

    article_num: RequiredString
    heading: str | None = None
    text: str | None = None
    text_status: str | None = None
    xml: str | None = None
    section: str | None = None
    section_heading: str | None = None


class Law(_ResponseModel):
    """A law lookup response."""

    sr_number: str | None = None
    abbreviation: str | None = None
    title: str | None = None
    consolidation_date: str | None = None
    language: str | None = None
    articles: list[LawArticle] | None = Field(default_factory=list)
    canton: str | None = None
    level: str | None = None
    snapshot_date: str | None = None
    version: str | None = None
    as_of: str | None = None
    text_status: str | None = None
    source_url: str | None = None
    source_label: str | None = None
    text_source: str | None = None
    pending_changes: list[dict[str, Any]] | None = None


class Court(_ResponseModel):
    """A court listing item."""

    court: RequiredString = Field(validation_alias=AliasChoices("court", "court_code"))
    name: str | None = None
    count: NonNegativeInt | None = Field(
        default=None, validation_alias=AliasChoices("count", "decision_count")
    )


class Citation(_ResponseModel):
    """A canonical citation response."""

    decision_id: str | None = None
    citation_string_de: str | None = None
    citation_string_fr: str | None = None
    citation_string_it: str | None = None
    canonical_url: str | None = None
    rule_statement: str | None = None
    exists: bool | None = Field(default=None, strict=True)
    queried: str | None = None
    resolved_id: str | None = None
    citation_string: str | None = None
    close_matches: list[DecisionSummary] | None = None
    joined_dockets: list[str] | None = None
    canonical_decision_id: str | None = None
    is_canonical: bool | None = Field(default=None, strict=True)
