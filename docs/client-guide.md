# OpenCaseLaw client guide

Detailed Python examples and client behavior. Start with the [README](../README.md) for installation
and a runnable example; see the [API compatibility notes](api-compatibility.md) for request
contracts and verification limits.

The examples below assume an open `client` inside a context manager, as in the README quick start.
API calls make live requests. Replace placeholder IDs and tokens with values from responses;
illustrative references may not resolve.

## Decisions

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

`search_decisions()` returns a `DecisionSearchResult` with `DecisionSummary` items. `get_decision()`
returns a `Decision`. Search accepts both `query` and `q` and forwards supplied values; the server
decides precedence. Read `total_is_lower_bound`, `degraded`, and `note` before interpreting the
result. Page only when `has_more` is true and `next_offset` is present; the requested `limit` may
differ from the returned count. A finished relevance search does not prove corpus completeness.
Absent continuation/uncertainty metadata stays `None`. If `total` or `limit` is omitted, the model
defaults it to the number of returned records; that fallback is not a corpus count.

Supplying `decision_type` raises `ValueError` locally; express that concept in `query`, or use
`court`/`chamber`. `find_relevant_erwaegung()` sends `top_k`; the old `max_paragraphs` Python
argument remains an alias.

Slash-containing docket references such as `4A_747/2012` are resolved through exact lookup before
fetching the canonical ID. Ambiguous, missing, or partial results raise `ValueError`; the client
does not choose an arbitrary hit.

## Docket lookup and tool discovery

```python
hits = client.lookup("BGE 140 III 86", exact=True, limit=5)
catalog = client.list_tools()  # {"tools": [{"name": ..., "inputSchema": ...}, ...]}
schema = client.get_openapi(research=True)
# Inspect the tool's inputSchema before calling it:
practice = client.call_tool("search_practice", {"query": "Mehrwertsteuer", "limit": 3})
```

Lookup `total` counts returned hits only (maximum 25); inspect all hits for ambiguity. `call_tool()`
raises `OpenCaseLawToolError` for `_is_error: true` responses, retaining the server details in
`.payload`. HTTP errors still raise `httpx.HTTPStatusError`.

## Courts, statistics, and health

```python
courts = client.list_courts()
statistics = client.get_statistics(court="bger", canton="CH", year=2024)
health = client.get_scraper_health()
integrity = client.get_integrity_proof("bger_4A_747_2012")
```

`list_courts()` returns the raw public API response, which may be a top-level array. Use
`list_court_models()` for parsed `Court` items.

## Citation graph and citation integrity

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

`Citation.exists` reports whether the reference resolved. For a requested passage, also inspect
`pinpoint_valid`, `pinpoint_status`, `pinpoint_note`, and `valid_pinpoints`. An invalid passage
returns an unpinpointed citation; do not append the rejected passage number. The saved response
fixture records the sample `2.3` pinpoint above as invalid for this BGE.

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

## Decision structure

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

## Statutes

```python
from opencaselaw import OpenCaseLawAPIError

try:
    cantonal_law = client.get_cantonal_law("StG", "ZH", article="12")
except OpenCaseLawAPIError as error:
    print(error.payload)  # Inspect the failure and any suggested candidates.
xml = client.get_law_xml("OR", article="41", language="de")
```

`get_law()` and `get_cantonal_law()` return a `Law` on success. A non-empty top-level `error`, even
in an HTTP 200 response, raises `OpenCaseLawAPIError`; inspect its `.payload` for details.
`get_law_xml()` requests `format=xml` and returns text. HTTP failures, including unavailable XML
(404), propagate. Article text can be missing or empty in tables of contents and historical
editions; inspect `text_status` and use `law.articles or []` when iterating. `get_commentary()`
accepts `canton`.

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

`get_law()` returns a `Law` with `LawArticle` items. `search_laws()` and `resolve_amendment_ref()`
return raw dictionaries without validating their nested fields.

## Legislation

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

## Commentaries, doctrine, and materials

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

## Research helpers

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

`mock_decision()` may return clarification questions instead of an outline. It sends the provided
facts and question to the public API and is not legal advice.

## Exports and feeds

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

## Scholarship

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

Scholarship search also accepts `q`, `source`, `pub_type`, `language`, `year_max`, and `author`. A
filter-only bibliographic browse does not need a topic query. Preserve `attributions`,
`license_usage`, and source-specific license terms when reusing results. Botschaft search accepts
`year_min` and `year_max`. Search methods for laws, commentaries, materials, legislation, and
Botschaften also accept `q`.

## Response models

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

The client uses frozen Pydantic models for stable high-use shapes and preserves the original
payload, including unknown fields, in each model's `raw` attribute. Invalid known fields raise
`pydantic.ValidationError` (a `ValueError` subclass), including malformed list entries; records are
never silently dropped. `raw` and nested collections remain mutable. Models support keyword
construction and `from_json()`; use `model_dump()` instead of dataclass utilities. Other JSON
wrappers return dictionaries, except `list_courts()`, which also accepts arrays, and
`list_court_models()`, which returns a list of `Court` models. JSON wrappers raise
`OpenCaseLawAPIError` for a non-empty top-level `error` in an HTTP-success response. `_is_error:
true` raises its subclass `OpenCaseLawToolError`. Both retain `.payload` without including server
text in the exception message. A completed citation miss (`exists: false`) or empty search remains a
successful result.

## Configuration

The checked-in `config.yaml` provides the package defaults shown below. Automatic loading reads only
its `opencaselaw` section in the current working directory and ignores unrelated application
settings. Set `auto_discover_config=False` to disable automatic loading. An explicit `config_path`
still loads a file, accepting either flat settings or an `opencaselaw` section. Missing files and
empty YAML documents use package defaults; unknown keys within client settings are rejected.
Constructor arguments such as `base_url`, `timeout`, and `rate_limit_delay` override configured
defaults. Every wrapper with a `limit` argument uses `default_limit` when it is omitted, including
lookup, citations, and mock decisions.

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

The default delay is `0.2` seconds between request starts per client instance. It does not
coordinate traffic across clients or processes. `request_timeout` overrides are available only on
decision search, relevant-Erwägung search, mock decisions, tool calls, and scholarship full-text
retrieval.

Client instances are intended for sequential use. HTTP and transport errors propagate to callers;
retries are not automatic. Configuration rejects non-finite timing values, non-positive limits, and
base URLs containing credentials, queries, or fragments. Close the client with a context manager or
`close()`.
