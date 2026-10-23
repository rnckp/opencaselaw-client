# OpenCaseLaw API compatibility notes

These notes describe the requests and response handling implemented by this independent client. They
are not an official service specification. Start with the [README](../README.md) for installation
and the [client guide](client-guide.md) for Python examples and configuration.

## Evidence and verification limits

The vendored [application schema](../tests/fixtures/application_openapi.json) and [typed research
schema](../tests/fixtures/research_openapi.json) were fetched on 2026-10-23.
[schema_manifest.json](../tests/fixtures/schema_manifest.json) records their source URLs, date, and
reproducible SHA-256 hashes of the stored files. The compact [request
contract](../tests/fixtures/public_api_contract.json) contains 51 public operations, all present in
the saved application schema; its other 11 operations are quota/billing/admin routes outside this
package's scope. The research schema describes seven routes, rather than the entire public request
contract.

Local contract tests check POST fields against the application body schemas using mock transport;
they do not execute POST requests against the service. Opt-in live tests cover schema drift,
populated core responses, slash-reference resolution, invalid pinpoint metadata, explicit
cantonal-law failure, publication and document-type filters, and representative public read routes.
On 2026-10-23, all 21 live cases passed against the public deployment; the offline suite passed
221 tests (live cases skipped). All 51 saved public operations remain in the deployed schema.
These bounded checks do not establish current availability of
every endpoint or exhaustive corpus coverage. The [selected response
fixture](../tests/fixtures/api_responses.json) records an invalid citation pinpoint, a cantonal-law
error, and a lookup hit; response coverage remains partial.

## Client compatibility behavior

- `query` and `q` are forwarded when supplied; precedence is server-side.
- `decision_type` is rejected locally. There is no `legal_area` argument.
- Relevant-Erwägung requests send `top_k`; `max_paragraphs` remains a Python alias. Conflicting values raise `ValueError`.
- Search models retain continuation, lower-bound, degraded-ranking, and query-condensation metadata. Missing optional metadata stays `None`. The client neither paginates automatically nor establishes exhaustive coverage.
- Publication filters use `published_from` and optional `published_to` (which requires `published_from`); `sort="published_desc"` sorts newest publications first. Inspect `publication_window_decided_from` for a server-imposed decision-date window; an earlier `date_from` widens it.
- `doc_type` filters `search_botschaft()` and the `botschaft_documents` returned by `get_materialien()`. On `search_materialien()` it is accepted and echoed but does not filter the curated digest.
- `Law.articles` can be absent or null, and article text can be absent, null, or empty. Inspect `text_status` and iterate over `articles or []`.
- JSON responses with a non-empty top-level `error` raise `OpenCaseLawAPIError`, retaining `.payload`. `_is_error: true` raises its subclass `OpenCaseLawToolError`. Completed citation misses (`exists: false`) and empty searches remain valid results.
- Slash-containing references passed to `get_decision()` use exact lookup before fetching a canonical ID. Missing, ambiguous, partial, malformed, or unroutable matches are rejected.
- Citation pinpoint validity, status, warnings, and valid alternatives are typed fields. `exists: true` does not mean the requested passage exists; invalid pinpoints return unpinpointed citation strings.

## Endpoint inventory

All paths below are relative to the default base URL, `https://mcp.opencaselaw.ch/api`. Path
parameters appear in braces. Numeric bounds below match the saved request contract; this client
generally leaves endpoint-specific validation to the server. The client uses its configured
`default_limit` (10 unless changed) when a wrapper limit is omitted, rather than reproducing each
server default.

| Method | Path | Query parameters | Numeric bounds |
| --- | --- | --- | --- |
| GET | `/openapi.json` | — | — |
| GET | `/research/openapi.json` | — | — |
| GET | `/lookup` | `q`, `query`, `limit`, `exact` | `limit`: 1–25 |
| POST | `/tool/{name}` | — | — |
| GET | `/tool` | — | — |
| GET | `/decisions` | `query`, `q`, `court`, `canton`, `language`, `date_from`, `date_to`, `published_from`, `published_to`, `chamber`, `marked_for_publication`, `limit`, `offset`, `sort`, `fields`, `include_pinpoint` | `limit`: 1–2000; `offset`: 0–unbounded |
| GET | `/decisions/{decision_id}` | `full_text` | — |
| GET | `/courts` | — | — |
| GET | `/integrity/{decision_id}` | — | — |
| GET | `/scraper-health` | — | — |
| GET | `/statistics` | `court`, `canton`, `year` | — |
| GET | `/citations/{decision_id}` | `direction`, `min_confidence`, `limit`, `offset` | `min_confidence`: 0–1; `limit`: 1–200; `offset`: 0–unbounded |
| GET | `/appeal-chain/{decision_id}` | `min_confidence` | `min_confidence`: 0–1 |
| GET | `/leading-cases` | `query`, `law_code`, `article`, `court`, `date_from`, `date_to`, `limit`, `include_pinpoint` | `limit`: 1–100 |
| GET | `/trends` | `query`, `law_code`, `article`, `court`, `date_from`, `date_to` | — |
| POST | `/mock-decision` | — | — |
| GET | `/laws/search` | `query`, `q`, `sr_number`, `canton`, `jurisdiction`, `language`, `limit` | `limit`: 1–50 |
| GET | `/laws/{abbreviation}` | `sr_number`, `article`, `language`, `canton`, `as_of`, `format` | — |
| GET | `/laws/{abbreviation}/{canton}` | `article`, `language` | — |
| GET | `/amendment-ref` | `ref_type`, `year`, `page` | — |
| GET | `/commentaries/search` | `query`, `q`, `abbreviation`, `language`, `limit` | `limit`: 1–50 |
| GET | `/commentaries/{abbreviation}` | `sr_number`, `article`, `language`, `canton` | — |
| GET | `/scholarship/search` | `query`, `q`, `source`, `pub_type`, `language`, `year_min`, `year_max`, `author`, `sort`, `limit` | `limit`: 1–50 |
| GET | `/scholarship/sources` | — | — |
| GET | `/scholarship/licenses` | — | — |
| GET | `/scholarship/citation-stats` | — | — |
| GET | `/scholarship/cited-by-statute` | `sr_number`, `article`, `limit` | `limit`: 1–100 |
| GET | `/scholarship/cited-by-decision` | `decision_id`, `limit` | `limit`: 1–100 |
| GET | `/scholarship-fulltext` | `pub_id` | — |
| GET | `/scholarship/{pub_id}` | — | — |
| GET | `/materialien/{law_code}` | `article`, `doc_type` | — |
| GET | `/materialien` | `query`, `q`, `law_code`, `limit`, `doc_type` | `limit`: 1–50 |
| GET | `/legislation/search` | `query`, `q`, `canton`, `language`, `limit`, `active_only`, `search_in_content`, `fetch_top_n_texts` | `limit`: 1–60; `fetch_top_n_texts`: 0–10 |
| GET | `/legislation/changes` | `canton`, `language` | — |
| GET | `/legislation/{lexfind_id}` | `systematic_number`, `canton`, `language`, `include_versions` | — |
| GET | `/doctrine` | `query` | — |
| GET | `/case-brief/{case}` | — | — |
| GET | `/cite` | `reference`, `pinpoint`, `language` | — |
| POST | `/attest` | — | — |
| POST | `/verify-claim` | — | — |
| GET | `/decisions/{decision_id}/export.docx` | — | — |
| GET | `/decisions/{decision_id}/export.pdf` | — | — |
| GET | `/decisions/{decision_id}/export.bib` | — | — |
| GET | `/decisions/{decision_id}/export.ris` | — | — |
| GET | `/atom/{court}.xml` | — | — |
| GET | `/erwaegung/{decision_id}/{e_number}` | — | — |
| GET | `/relevant-erwaegung/{decision_id}` | `claim`, `top_k` | `top_k`: 1–10 |
| GET | `/article-purpose/{sr_number}/{article}` | `language`, `max_paragraphs` | `max_paragraphs`: 1–20 |
| GET | `/search-botschaft` | `query`, `q`, `language`, `year_min`, `year_max`, `doc_type`, `limit` | `limit`: 1–50 |
| GET | `/article-history/{sr_number}/{article}` | `language`, `leading_cases_limit` | `leading_cases_limit`: 1–15 |
| GET | `/regeste/{decision_id}` | — | — |
| GET | `/structure/{decision_id}` | `paragraph_excerpt_chars` | `paragraph_excerpt_chars`: 50–5000 |
| GET | `/exam-question` | `topic`, `exclude_ids` | — |

`get_openapi()` selects the application or research schema route. These two discovery routes are
implemented and tested separately but are not included in the saved contract.

### JSON request bodies

These fields are sent by the wrappers; required fields below are required Python arguments. The POST
contract tests compare body field coverage, required fields, top-level types, and transport
serialization with the vendored application schema; they do not validate all nested values or
server-side constraints.

- `/mock-decision`: `facts` (required), `question`, `deciding_court`, `preferred_language`, `statute_references`, `clarifications`, `fedlex_urls`, `limit`.
- `/attest`: `redacted_text`, `draft_text`, `audit_grounding`, `audit_quotes`, `client_redactor_version`, `client_redactor_summary`.
- `/verify-claim`: `claim` (required), `decision_id` (required), `pinpoint`.
- `/tool/{name}` receives the supplied argument object directly; inspect the tool’s current `inputSchema` first and do not wrap it in an `arguments` property.

## Scope and contract tests

This package provides synchronous HTTP wrappers. It has no CLI entry point, local packs, offline
research checks, or evidence-bundle implementation. Billing, quota, license-key, and admin wrappers
are outside its scope. `call_tool()` accepts a tool name and arguments without local catalog/schema
validation; available tools depend on the service.

`test_api_contract.py` compares GET requests with the saved contract, and `test_schema_snapshots.py`
checks the vendored schema hashes, POST bodies, selected response fixtures, and required typed
research fields. Client tests cover XML, schema retrieval, error handling, and ambiguity rejection
with local transports. Run `uv run pytest --live-api tests/opencaselaw/test_live_api.py` to check
deployment drift and representative live behavior explicitly. Default tests never contact the
service; manual CI dispatch can enable the live suite. These tests do not validate every response
field or execute POST research workflows.
