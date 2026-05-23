"""Synchronous client for the public OpenCaseLaw REST API."""

import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from .config import OpenCaseLawConfig, _normalize_config_values, load_config
from .models import Citation, Court, Decision, DecisionSearchResult, Law


def _quote_segment(value: str | int) -> str:
    return quote(str(value), safe="")


def _params(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


class OpenCaseLawClient:
    """Client for the public no-key OpenCaseLaw API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        rate_limit_delay: float | None = None,
        config_path: Path | str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize the client."""
        self.config = load_config(config_path)
        effective_config = OpenCaseLawConfig(
            **_normalize_config_values(
                {
                    "base_url": base_url or self.config.base_url,
                    "timeout": timeout if timeout is not None else self.config.timeout,
                    "rate_limit_delay": (
                        rate_limit_delay
                        if rate_limit_delay is not None
                        else self.config.rate_limit_delay
                    ),
                    "default_limit": self.config.default_limit,
                }
            )
        )
        self.config = effective_config
        self.base_url = effective_config.base_url
        self.timeout = effective_config.timeout
        self.rate_limit_delay = effective_config.rate_limit_delay
        self._last_request_time = 0.0
        self._client = httpx.Client(timeout=self.timeout, transport=transport)

    def __enter__(self) -> "OpenCaseLawClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _rate_limit(self) -> None:
        if self.rate_limit_delay <= 0:
            return
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _limit(self, value: int | None) -> int:
        return self.config.default_limit if value is None else value

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        self._rate_limit()
        request_kwargs: dict[str, Any] = {
            "params": params,
            "json": json_data,
        }
        if timeout is not None:
            request_kwargs["timeout"] = timeout
        response = self._client.request(method, self._url(path), **request_kwargs)
        response.raise_for_status()
        return response

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        data = self._request("GET", path, params=params, timeout=timeout).json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object from {path}")
        return data

    def _post_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        data = self._request(
            "POST",
            path,
            params=params,
            json_data=json_data,
            timeout=timeout,
        ).json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object from {path}")
        return data

    def _get_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        return self._request("GET", path, params=params).content

    def _get_text(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> str:
        return self._request("GET", path, params=params).text

    # Case law

    def search_decisions(
        self,
        query: str | None = None,
        court: str | None = None,
        canton: str | None = None,
        language: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        chamber: str | None = None,
        decision_type: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        sort: str | None = None,
        fields: str | None = None,
        *,
        request_timeout: float | None = None,
    ) -> DecisionSearchResult:
        """Search court decisions."""
        data = self._get_json(
            "/decisions",
            params=_params(
                query=query,
                court=court,
                canton=canton,
                language=language,
                date_from=date_from,
                date_to=date_to,
                chamber=chamber,
                decision_type=decision_type,
                limit=self._limit(limit),
                offset=offset,
                sort=sort,
                fields=fields,
            ),
            timeout=request_timeout,
        )
        return DecisionSearchResult.from_json(data)

    def get_decision(self, decision_id: str, full_text: bool = True) -> Decision:
        """Fetch a single decision by ID, docket number, or BGE reference."""
        data = self._get_json(
            f"/decisions/{_quote_segment(decision_id)}",
            params=_params(full_text=full_text),
        )
        return Decision.from_json(data)

    def list_courts(self) -> dict[str, Any] | list[Any]:
        """List available courts."""
        data = self._request("GET", "/courts").json()
        if not isinstance(data, (dict, list)):
            raise ValueError("Expected JSON object or array from /courts")
        return data

    def list_court_models(self) -> list[Court]:
        """List available courts as parsed court items when the response is a list."""
        data = self.list_courts()
        if isinstance(data, list):
            return [Court.from_json(item) for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            courts = data.get("courts", [])
            if isinstance(courts, list):
                return [
                    Court.from_json(item) for item in courts if isinstance(item, dict)
                ]
        return []

    def get_statistics(
        self,
        court: str | None = None,
        canton: str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """Get aggregate corpus statistics."""
        return self._get_json(
            "/statistics",
            params=_params(court=court, canton=canton, year=year),
        )

    def get_scraper_health(self) -> dict[str, Any]:
        """Get per-source scraper health."""
        return self._get_json("/scraper-health")

    def get_integrity_proof(self, decision_id: str) -> dict[str, Any]:
        """Get an integrity proof for a decision."""
        return self._get_json(f"/integrity/{_quote_segment(decision_id)}")

    # Citation graph and analysis

    def get_citations(
        self,
        decision_id: str,
        direction: str | None = None,
        min_confidence: float | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Find citations for a decision."""
        return self._get_json(
            f"/citations/{_quote_segment(decision_id)}",
            params=_params(
                direction=direction,
                min_confidence=min_confidence,
                limit=self._limit(limit),
            ),
        )

    def get_appeal_chain(
        self,
        decision_id: str,
        min_confidence: float | None = None,
    ) -> dict[str, Any]:
        """Trace a decision's appeal chain."""
        return self._get_json(
            f"/appeal-chain/{_quote_segment(decision_id)}",
            params=_params(min_confidence=min_confidence),
        )

    def find_leading_cases(
        self,
        query: str | None = None,
        law_code: str | None = None,
        article: str | None = None,
        court: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Find highly cited decisions for a topic or statute."""
        return self._get_json(
            "/leading-cases",
            params=_params(
                query=query,
                law_code=law_code,
                article=article,
                court=court,
                date_from=date_from,
                date_to=date_to,
                limit=self._limit(limit),
            ),
        )

    def analyze_trends(
        self,
        query: str | None = None,
        law_code: str | None = None,
        article: str | None = None,
        court: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Analyze decision counts over time."""
        return self._get_json(
            "/trends",
            params=_params(
                query=query,
                law_code=law_code,
                article=article,
                court=court,
                date_from=date_from,
                date_to=date_to,
            ),
        )

    # Statutes, legislation, commentaries, and materials

    def search_laws(
        self,
        query: str,
        sr_number: str | None = None,
        canton: str | None = None,
        jurisdiction: str | None = None,
        language: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Search Swiss statute articles."""
        return self._get_json(
            "/laws/search",
            params=_params(
                query=query,
                sr_number=sr_number,
                canton=canton,
                jurisdiction=jurisdiction,
                language=language,
                limit=self._limit(limit),
            ),
        )

    def get_law(
        self,
        abbreviation: str,
        sr_number: str | None = None,
        article: str | None = None,
        language: str | None = None,
        canton: str | None = None,
        as_of: str | None = None,
    ) -> Law:
        """Look up a Swiss law by abbreviation or SR number."""
        data = self._get_json(
            f"/laws/{_quote_segment(abbreviation)}",
            params=_params(
                sr_number=sr_number,
                article=article,
                language=language,
                canton=canton,
                as_of=as_of,
            ),
        )
        return Law.from_json(data)

    def resolve_amendment_ref(
        self, ref_type: str, year: int, page: int
    ) -> dict[str, Any]:
        """Resolve an AS/BBl/RO/RU/FF reference to a Fedlex ELI URI."""
        return self._get_json(
            "/amendment-ref",
            params=_params(ref_type=ref_type, year=year, page=page),
        )

    def search_commentaries(
        self,
        query: str,
        abbreviation: str | None = None,
        language: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Search scholarly commentaries."""
        return self._get_json(
            "/commentaries/search",
            params=_params(
                query=query,
                abbreviation=abbreviation,
                language=language,
                limit=self._limit(limit),
            ),
        )

    def get_commentary(
        self,
        abbreviation: str,
        sr_number: str | None = None,
        article: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Get commentary for a law article."""
        return self._get_json(
            f"/commentaries/{_quote_segment(abbreviation)}",
            params=_params(sr_number=sr_number, article=article, language=language),
        )

    def search_materialien(
        self,
        query: str,
        law_code: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Search preparatory materials."""
        return self._get_json(
            "/materialien",
            params=_params(query=query, law_code=law_code, limit=self._limit(limit)),
        )

    def get_materialien(
        self,
        law_code: str,
        article: str | None = None,
    ) -> dict[str, Any]:
        """Get preparatory materials for a law article."""
        return self._get_json(
            f"/materialien/{_quote_segment(law_code)}",
            params=_params(article=article),
        )

    def search_legislation(
        self,
        query: str,
        canton: str | None = None,
        language: str | None = None,
        limit: int | None = None,
        active_only: bool | None = None,
        search_in_content: bool | None = None,
        fetch_top_n_texts: int | None = None,
    ) -> dict[str, Any]:
        """Search Swiss legislation."""
        return self._get_json(
            "/legislation/search",
            params=_params(
                query=query,
                canton=canton,
                language=language,
                limit=self._limit(limit),
                active_only=active_only,
                search_in_content=search_in_content,
                fetch_top_n_texts=fetch_top_n_texts,
            ),
        )

    def get_legislation(
        self,
        lexfind_id: int,
        systematic_number: str | None = None,
        canton: str | None = None,
        language: str | None = None,
        include_versions: bool | None = None,
    ) -> dict[str, Any]:
        """Get legislation details by LexFind ID."""
        return self._get_json(
            f"/legislation/{_quote_segment(lexfind_id)}",
            params=_params(
                systematic_number=systematic_number,
                canton=canton,
                language=language,
                include_versions=include_versions,
            ),
        )

    def get_legislation_changes(
        self,
        canton: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Browse recent legislation changes."""
        return self._get_json(
            "/legislation/changes",
            params=_params(canton=canton, language=language),
        )

    def get_doctrine(self, query: str) -> dict[str, Any]:
        """Get doctrine for a legal topic."""
        return self._get_json("/doctrine", params=_params(query=query))

    # Research and citation integrity

    def get_case_brief(self, case: str) -> dict[str, Any]:
        """Get a structured case brief."""
        return self._get_json(f"/case-brief/{_quote_segment(case)}")

    def cite(
        self,
        reference: str,
        pinpoint: str | None = None,
        language: str | None = None,
    ) -> Citation:
        """Build a canonical Swiss citation."""
        data = self._get_json(
            "/cite",
            params=_params(reference=reference, pinpoint=pinpoint, language=language),
        )
        return Citation.from_json(data)

    def attest(
        self,
        redacted_text: str | None = None,
        draft_text: str | None = None,
        audit_grounding: bool | None = None,
        audit_quotes: bool | None = None,
        client_redactor_version: str | None = None,
        client_redactor_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Audit a draft for invalid citations."""
        return self._post_json(
            "/attest",
            json_data=_params(
                redacted_text=redacted_text,
                draft_text=draft_text,
                audit_grounding=audit_grounding,
                audit_quotes=audit_quotes,
                client_redactor_version=client_redactor_version,
                client_redactor_summary=client_redactor_summary,
            ),
        )

    def verify_claim(
        self,
        claim: str,
        decision_id: str,
        pinpoint: str | None = None,
    ) -> dict[str, Any]:
        """Verify whether a decision supports a legal claim."""
        return self._post_json(
            "/verify-claim",
            json_data=_params(
                claim=claim,
                decision_id=decision_id,
                pinpoint=pinpoint,
            ),
        )

    def mock_decision(
        self,
        facts: str,
        question: str | None = None,
        deciding_court: str | None = None,
        preferred_language: str | None = None,
        statute_references: list[dict[str, Any]] | None = None,
        clarifications: list[dict[str, Any]] | None = None,
        fedlex_urls: list[str] | None = None,
        limit: int | None = None,
        *,
        request_timeout: float | None = None,
    ) -> dict[str, Any]:
        """Draft a research-only mock decision outline."""
        return self._post_json(
            "/mock-decision",
            json_data=_params(
                facts=facts,
                question=question,
                deciding_court=deciding_court,
                preferred_language=preferred_language,
                statute_references=statute_references,
                clarifications=clarifications,
                fedlex_urls=fedlex_urls,
                limit=self._limit(limit),
            ),
            timeout=request_timeout,
        )

    def generate_exam_question(
        self,
        topic: str,
        exclude_ids: str | None = None,
    ) -> dict[str, Any]:
        """Generate a law exam question from a real BGE fact pattern."""
        return self._get_json(
            "/exam-question",
            params=_params(topic=topic, exclude_ids=exclude_ids),
        )

    # Decision structure

    def get_regeste(self, decision_id: str) -> dict[str, Any]:
        """Get the official Regeste for a decision."""
        return self._get_json(f"/regeste/{_quote_segment(decision_id)}")

    def get_structure(
        self,
        decision_id: str,
        paragraph_excerpt_chars: int | None = None,
    ) -> dict[str, Any]:
        """Get structured decision sections."""
        return self._get_json(
            f"/structure/{_quote_segment(decision_id)}",
            params=_params(paragraph_excerpt_chars=paragraph_excerpt_chars),
        )

    def get_erwaegung(self, decision_id: str, e_number: str) -> dict[str, Any]:
        """Get the verbatim text of one Erwägung."""
        return self._get_json(
            f"/erwaegung/{_quote_segment(decision_id)}/{_quote_segment(e_number)}"
        )

    def find_relevant_erwaegung(
        self,
        decision_id: str,
        claim: str,
        max_paragraphs: int | None = None,
    ) -> dict[str, Any]:
        """Find Erwägungen matching a legal claim."""
        return self._get_json(
            f"/relevant-erwaegung/{_quote_segment(decision_id)}",
            params=_params(claim=claim, max_paragraphs=max_paragraphs),
        )

    # Materialien v2-style helpers from the public spec

    def get_article_purpose(
        self,
        sr_number: str,
        article: str,
        language: str | None = None,
        max_paragraphs: int | None = None,
    ) -> dict[str, Any]:
        """Get Botschaft text explaining an article's purpose."""
        return self._get_json(
            f"/article-purpose/{_quote_segment(sr_number)}/{_quote_segment(article)}",
            params=_params(language=language, max_paragraphs=max_paragraphs),
        )

    def search_botschaft(
        self,
        query: str,
        language: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Search the verbatim Botschaft corpus."""
        return self._get_json(
            "/search-botschaft",
            params=_params(query=query, language=language, limit=self._limit(limit)),
        )

    def get_article_history(
        self,
        sr_number: str,
        article: str,
        language: str | None = None,
        leading_cases_limit: int | None = None,
    ) -> dict[str, Any]:
        """Get a chronological timeline for a statute article."""
        return self._get_json(
            f"/article-history/{_quote_segment(sr_number)}/{_quote_segment(article)}",
            params=_params(
                language=language,
                leading_cases_limit=leading_cases_limit,
            ),
        )

    # Exports

    def export_docx(self, decision_id: str) -> bytes:
        """Download a decision as a Word document."""
        return self._get_bytes(f"/decisions/{_quote_segment(decision_id)}/export.docx")

    def export_pdf(self, decision_id: str) -> bytes:
        """Download a decision as a PDF."""
        return self._get_bytes(f"/decisions/{_quote_segment(decision_id)}/export.pdf")

    def export_bib(self, decision_id: str) -> str:
        """Download a decision as a BibTeX entry."""
        return self._get_text(f"/decisions/{_quote_segment(decision_id)}/export.bib")

    def export_ris(self, decision_id: str) -> str:
        """Download a decision as a RIS record."""
        return self._get_text(f"/decisions/{_quote_segment(decision_id)}/export.ris")

    def atom_feed(self, court: str) -> str:
        """Get the Atom feed for a court."""
        return self._get_text(f"/atom/{_quote_segment(court)}.xml")
