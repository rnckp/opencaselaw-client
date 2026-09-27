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

    @model_validator(mode="before")
    @classmethod
    def _default_counts(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("results", []), list):
            count = len(data.get("results", []))
            return {"total": count, "limit": count, **data}
        return data


class Decision(DecisionSummary):
    """A full decision response."""

    docket_number: str | None = None
    full_text: str | None = None


class LawArticle(_ResponseModel):
    """A statute article returned by a law lookup."""

    article_num: RequiredString
    heading: str | None = None
    text: RequiredString


class Law(_ResponseModel):
    """A law lookup response."""

    sr_number: str | None = None
    abbreviation: str | None = None
    title: str | None = None
    consolidation_date: str | None = None
    language: str | None = None
    articles: list[LawArticle] = Field(default_factory=list)


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
