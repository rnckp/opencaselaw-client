# OpenCaseLaw Python Client

**Python client for accessing the public no-key [OpenCaseLaw](https://opencaselaw.ch) REST API more easily.**

This project is not official, associated with, or affiliated with OpenCaseLaw. It was developed independently as a convenience wrapper around the publicly documented OpenCaseLaw API.

**Note:** The official [OpenCaseLaw website](https://opencaselaw.ch) and [API documentation](https://opencaselaw.ch/api) are the actual and authoritative reference for the API.

## Installation from a checkout

Requires Python 3.13 or newer and `uv`. Run from the repository root:

```bash
uv sync
```

## Quick Start

For a broader tour of the public API, see [examples/opencaselaw_demo.ipynb](examples/opencaselaw_demo.ipynb).

```python
from opencaselaw import OpenCaseLawClient

with OpenCaseLawClient() as client:
    # Search for court decisions
    results = client.search_decisions(
        query="Mietrecht Kündigung",
        court="bger",
        language="de",
        limit=5,
    )

    for decision in results.results:
        print(decision.citation_string_de, decision.canonical_url)

    # Fetch a decision
    decision = client.get_decision("bger_4A_747_2012")
    print(decision.title)

    # Look up a statute article
    law = client.get_law("OR", article="41", language="de")
    for article in law.articles or []:
        print(article.article_num, article.text, article.text_status)

    # Build a canonical citation
    citation = client.cite("BGE 140 III 86", pinpoint="2.3")
    print(citation.citation_string_de)
```

## API Reference

The [compatibility reference](docs/api-compatibility.md) lists wrapper routes and parameters against the checked-in contract dated 2026-09-27, with verification limits. It does not establish current service availability or complete API coverage.

The examples below assume an open `client` inside a `with OpenCaseLawClient() as client:` block, as in Quick Start. They make live requests; example IDs and references are illustrative and may not resolve.

### Decisions

```python
results = client.search_decisions(
    query="Arbeitsvertrag Kündigung",
    court="bger",  # court code, e.g. "bger", "bvger"
    canton="CH",  # "CH", "ZH", "BE", ...
    language="de",  # "de", "fr", "it", "rm"
    date_from="2020-01-01",
    date_to="2024-12-31",
    chamber="I",  # optional chamber substring
    limit=20,
    offset=0,
    sort="date_desc",  # "relevance", "date_desc", "date_asc"
    fields="compact",  # "full" or "compact"
    include_pinpoint=False,  # skip extra passage lookups
    marked_for_publication=None,  # True: BGer rulings marked for the BGE collection
    request_timeout=60.0,  # optional per-call timeout for slow broad searches
)

decision = client.get_decision("bger_4A_747_2012", full_text=True)
```

`search_decisions()` returns a `DecisionSearchResult` with `DecisionSummary` items. `get_decision()` returns a `Decision`. Search accepts both `query` and `q` and forwards supplied values; the server decides precedence. Read `total_is_lower_bound`, `degraded`, and `note` before interpreting the result. Page only when `has_more` is true and `next_offset` is present; the requested `limit` may differ from the returned count. A finished relevance search does not prove corpus completeness. Absent continuation/uncertainty metadata stays `None`. If `total` or `limit` is omitted, the model defaults it to the number of returned records; that fallback is not a corpus count.

Supplying `decision_type` raises `ValueError` locally; express that concept in `query`, or use `court`/`chamber`. `find_relevant_erwaegung()` sends `top_k`; the old `max_paragraphs` Python argument remains an alias.

### Docket Lookup and Tool Discovery

```python
hits = client.lookup("BGE 140 III 86", exact=True, limit=5)
catalog = client.list_tools()  # {"tools": [{"name": ..., "inputSchema": ...}, ...]}
schema = client.get_openapi(research=True)
# Inspect the tool's inputSchema before calling it:
practice = client.call_tool("search_practice", {"query": "Mehrwertsteuer", "limit": 3})
```

Lookup `total` counts returned hits only (maximum 25); inspect all hits for ambiguity. `call_tool()` raises `OpenCaseLawToolError` for `_is_error: true` responses, retaining the server details in `.payload`. HTTP errors still raise `httpx.HTTPStatusError`.

### Courts, Statistics, and Health

```python
courts = client.list_courts()
statistics = client.get_statistics(court="bger", canton="CH", year=2024)
health = client.get_scraper_health()
integrity = client.get_integrity_proof("bger_4A_747_2012")
```

`list_courts()` returns the raw public API response, which may be a top-level array. Use `list_court_models()` for parsed `Court` items.

### Citation Graph and Citation Integrity

```python
citation = client.cite("BGE 140 III 86", pinpoint="2.3", language="de")
citations = client.get_citations(
    "bger_4A_747_2012",
    direction="both",  # "both", "outgoing", "incoming"
    min_confidence=0.3,
    limit=50,
    offset=0,  # follow returned next_offset and per-direction has_more flags
)
appeal_chain = client.get_appeal_chain("bger_4A_747_2012")
leading = client.find_leading_cases(query="Mietrecht Kündigung", court="bger", limit=10)
trends = client.analyze_trends(query="Datenschutz", court="bger")
```

Audit and claim verification endpoints:

```python
attestation = client.attest(
    draft_text="Gemäss BGE 140 III 86 E. 2.3 gilt ...",
    audit_grounding=False,
    audit_quotes=False,
)

claim_check = client.verify_claim(
    claim="Die Kündigung eines Mietvertrags darf nicht rechtsmissbräuchlich sein.",
    decision_id="bger_4A_747_2012",
    pinpoint="2.3",
)
```

Do not send confidential or personal data to public API endpoints.

### Decision Structure

```python
regeste = client.get_regeste("bger_4A_747_2012")
structure = client.get_structure("bger_4A_747_2012", paragraph_excerpt_chars=500)
erwaegung = client.get_erwaegung("bger_4A_747_2012", "2.3")
relevant = client.find_relevant_erwaegung(
    "bger_4A_747_2012",
    claim="The decision supports this legal proposition.",
    top_k=5,
    request_timeout=120.0,  # optional extra time for this endpoint
)
```

### Statutes

```python
cantonal_law = client.get_cantonal_law("StG", "ZH", article="12")
print(cantonal_law.raw)  # Inspect error/candidates if the abbreviation does not resolve.
xml = client.get_law_xml("OR", article="41", language="de")
```

`get_law()` returns a `Law`; `get_law_xml()` requests `format=xml` and returns text. HTTP failures, including unavailable XML (404), propagate. A successful HTTP response can still contain an application error: inspect `law.raw` for `error`, `note`, and `candidates`, especially for ambiguous cantonal abbreviations. Article text can be missing or empty in tables of contents and historical editions; inspect `text_status` and use `law.articles or []` when iterating. `get_commentary()` accepts `canton`.

```python
law = client.get_law("OR", article="41", language="de")
search_hits = client.search_laws(
    query="Schadenersatz",
    sr_number="220",
    canton="CH",
    jurisdiction="federal",  # "all", "federal", "cantonal"
    language="de",
    limit=10,
)
amendment = client.resolve_amendment_ref(ref_type="BBl", year=2020, page=1)
```

`get_law()` returns a `Law` with `LawArticle` items. `search_laws()` and `resolve_amendment_ref()` return raw dictionaries without validating their nested fields.

### Legislation

```python
legislation_hits = client.search_legislation(
    query="Datenschutz",
    canton="CH",
    language="de",
    limit=20,
    active_only=True,
    search_in_content=False,
    fetch_top_n_texts=0,
)
legislation = client.get_legislation(
    12345,  # placeholder: replace with a LexFind ID from a search result
    systematic_number=None,
    canton="CH",
    language="de",
    include_versions=False,
)
changes = client.get_legislation_changes(canton="CH", language="de")
```

### Commentaries, Doctrine, and Materials

```python
commentary_hits = client.search_commentaries(
    query="Schadenersatz",
    abbreviation="OR",
    language="de",
    limit=10,
)
commentary = client.get_commentary("OR", article="41", language="de")
doctrine = client.get_doctrine("Art. 41 OR Schadenersatz")

materials = client.search_materialien(query="Haftung", law_code="OR", limit=10)
article_materials = client.get_materialien("OR", article="41")
purpose = client.get_article_purpose("220", "41", language="de", max_paragraphs=8)
botschaft = client.search_botschaft("Schadenersatz", language="de", limit=20)
history = client.get_article_history("220", "41", language="de")
```

### Research Helpers

```python
brief = client.get_case_brief("BGE 140 III 86")
exam = client.generate_exam_question("Vertragsrecht")
mock = client.mock_decision(
    facts="Eine Mieterin kündigt nach einer strittigen Nebenkostenabrechnung fristlos.",
    question="Welche zivilrechtlichen Fragen stellen sich?",
    preferred_language="de",
    limit=5,
    request_timeout=120.0,
)
```

`mock_decision()` may return clarification questions instead of an outline. It sends the provided facts and question to the public API and is not legal advice.

### Exports and Feeds

```python
from pathlib import Path

docx = client.export_docx("bger_4A_747_2012")
pdf = client.export_pdf("bger_4A_747_2012")
bib = client.export_bib("bger_4A_747_2012")
ris = client.export_ris("bger_4A_747_2012")
feed = client.atom_feed("bger")

Path("decision.docx").write_bytes(docx)
Path("decision.pdf").write_bytes(pdf)
Path("decision.bib").write_text(bib, encoding="utf-8")
Path("decision.ris").write_text(ris, encoding="utf-8")
```

### Configuration

Runtime defaults are loaded from `config.yaml` in the current working directory, or from the constructor's `config_path`. Missing files and empty YAML documents use package defaults. The settings can be top-level or nested under `opencaselaw`; unknown setting keys are rejected. Constructor arguments such as `base_url`, `timeout`, and `rate_limit_delay` override configured defaults. Every wrapper with a `limit` argument uses `default_limit` when it is omitted, including lookup, citations, and mock decisions.

```yaml
opencaselaw:
  base_url: "https://mcp.opencaselaw.ch/api"
  timeout: 30.0
  rate_limit_delay: 0.2
  default_limit: 10
```

```python
with OpenCaseLawClient(timeout=10.0, rate_limit_delay=0.5) as client:
    print(client.config)
```

The default delay is `0.2` seconds between request starts per client instance. It does not coordinate traffic across clients or processes. `request_timeout` overrides are available only on decision search, relevant-Erwägung search, mock decisions, tool calls, and scholarship full-text retrieval.

### Scholarship

```python
sources = client.list_scholarship_sources()
licenses = client.get_scholarship_licenses()
hits = client.search_scholarship("Mietrecht", year_min=2020, sort="year", limit=5)
statute_links = client.find_scholarship_citing_statute("220", article="41", limit=5)
decision_links = client.find_scholarship_citing_decision("bge_BGE_140_III_86", limit=5)
stats = client.get_scholarship_citation_stats()
# Use a pub_id returned by search:
# publication = client.get_scholarship(pub_id)
# full_text = client.get_scholarship_full_text(pub_id, request_timeout=120.0)
```

Scholarship search also accepts `q`, `source`, `pub_type`, `language`, `year_max`, and `author`. A filter-only bibliographic browse does not need a topic query. Preserve `attributions`, `license_usage`, and source-specific license terms when reusing results. Botschaft search accepts `year_min` and `year_max`. Search methods for laws, commentaries, materials, legislation, and Botschaften also accept `q`.

### Typed Models

```python
from opencaselaw import (
    Citation,
    Court,
    Decision,
    DecisionSearchResult,
    DecisionSummary,
    Law,
    LawArticle,
)
```

The client uses frozen Pydantic models for stable high-use shapes and preserves the original payload, including unknown fields, in each model's `raw` attribute. Invalid known fields raise `pydantic.ValidationError` (a `ValueError` subclass), including malformed list entries; records are never silently dropped. `raw` and nested collections remain mutable. Models support keyword construction and `from_json()`; use `model_dump()` instead of dataclass utilities. Other JSON wrappers return dictionaries, except `list_courts()`, which also accepts arrays, and `list_court_models()`, which returns a list of `Court` models. Only `call_tool()` translates `_is_error: true` into a tool exception; HTTP-success error payloads from other routes are retained, including in model `raw` fields.

## Scope

This synchronous library wraps the routes listed in the [compatibility reference](docs/api-compatibility.md). It has no CLI, async client, or application server. License, payment, and private/admin routes that may appear in the raw OpenAPI schema are intentionally out of scope.

Covered endpoint groups:

- Decisions, docket lookup, courts, statistics, scraper health, and integrity proofs
- Scholarship, schema retrieval, and research tool discovery/calls
- Citation graph, appeal chains, leading cases, trends, citation building, attestation, and claim verification
- Decision structure, Regeste, Erwägungen, and relevant Erwägungen
- Laws, legislation, commentaries, doctrine, materials, article purpose, Botschaft search, and article history
- Case briefs, exam questions, mock decisions, exports, and Atom feeds

## Data Sources

The repository does not establish current corpus coverage. Query the service for reported coverage:

```python
courts = client.list_courts()
statistics = client.get_statistics()
health = client.get_scraper_health()
```

## Fair Use

This independent client accesses public OpenCaseLaw endpoints.

> [!IMPORTANT]
> Please be kind to the server, keep rate limiting enabled for batch work, mention OpenCaseLaw as the data source when appropriate, and avoid sending confidential or personal data to public endpoints. **Also consider contributing or donating to [OpenCaseLaw](https://opencaselaw.ch/).**

## Development

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run pytest -v
uv build
```

Source lives in `src/opencaselaw`, with package tests in `tests/opencaselaw`. `uv sync` installs the package in editable mode; no `PYTHONPATH` override is needed. The `uv_build` backend produces a wheel and source distribution in `dist/`. Package metadata requires Python 3.13 or newer; there is no CI matrix verifying the supported range. Tests use local mock transports and do not call the public API; the demo notebook does. Weekly dependency updates are configured in `.github/dependabot.yml`, but no CI workflows or pre-commit hooks are configured. See [PLAN.md](PLAN.md) for follow-up work.

Client instances are intended for sequential use. The delay is per client, not a shared per-IP limiter. HTTP errors and transport errors propagate to callers; retries are not automatic. Configuration rejects non-finite timing values, non-positive limits, and base URLs containing credentials, queries, or fragments.

## License

This Python client is licensed under the MIT License.

The MIT License applies only to this client code. It does not apply to OpenCaseLaw data, API content, court decisions, statutes, commentaries, or other source materials returned by the service. For data and content licensing details, consult [OpenCaseLaw](https://opencaselaw.ch) and the respective original data sources.
