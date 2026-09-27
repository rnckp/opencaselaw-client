# Public API compatibility reference

## Evidence and verification limits

This reference was checked against `src/opencaselaw/client.py`, its tests, and the [request-contract fixture](../tests/fixtures/public_api_contract.json). The fixture records an application-schema source URL, a check date of 2026-09-27, and a SHA-256 value. It contains selected methods, paths, and parameter schemas, but no response schemas or POST body schemas. The original schema is not stored, so its hash cannot be independently reproduced from this repository.

The previous audit cited the deployed application and typed research schemas, tool catalog, and upstream commit `05a6dcd1f7c24ba4091d8ae254dc7975e1589db6`. Those sources are not vendored here; current deployment behavior and upstream-source claims were not reverified in this repository-only review. Saved notebook outputs illustrate earlier responses, including failures; they are not repeatable service checks.

## Client compatibility behavior

- `query` and `q` are forwarded when supplied; precedence is server-side.
- `decision_type` is rejected locally. There is no `legal_area` argument.
- Relevant-Erwägung requests send `top_k`; `max_paragraphs` remains a Python alias. Conflicting values raise `ValueError`.
- Search models retain continuation, lower-bound, degraded-ranking, and query-condensation metadata. Missing optional metadata stays `None`. The client neither paginates automatically nor establishes exhaustive coverage.
- `Law.articles` can be absent or null, and article text can be absent, null, or empty. Inspect `text_status` and iterate over `articles or []`.
- Tool responses marked `_is_error: true` raise `OpenCaseLawToolError`, retaining `.payload`. Other HTTP-success error payloads are not automatically raised; dictionaries and model `raw` fields retain them.

## Endpoint inventory

All paths below are relative to `https://mcp.opencaselaw.ch/api`. Path parameters appear in braces. Numeric bounds below come from the saved contract, not a fresh deployment check; this client generally leaves endpoint-specific validation to the server. The client uses its configured `default_limit` (10 unless changed) when a wrapper limit is omitted, rather than reproducing each server default.

| Method | Path | Query parameters | Numeric bounds |
| --- | --- | --- | --- |
| GET | `/openapi.json` | — | — |
| GET | `/research/openapi.json` | — | — |
| GET | `/lookup` | `q`, `query`, `limit`, `exact` | `limit`: 1–25 |
| POST | `/tool/{name}` | — | — |
| GET | `/tool` | — | — |
| GET | `/decisions` | `query`, `q`, `court`, `canton`, `language`, `date_from`, `date_to`, `chamber`, `marked_for_publication`, `limit`, `offset`, `sort`, `fields`, `include_pinpoint` | `limit`: 1–2000; `offset`: 0–unbounded |
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
| GET | `/materialien/{law_code}` | `article` | — |
| GET | `/materialien` | `query`, `q`, `law_code`, `limit` | `limit`: 1–50 |
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
| GET | `/search-botschaft` | `query`, `q`, `language`, `year_min`, `year_max`, `limit` | `limit`: 1–50 |
| GET | `/article-history/{sr_number}/{article}` | `language`, `leading_cases_limit` | `leading_cases_limit`: 1–15 |
| GET | `/regeste/{decision_id}` | — | — |
| GET | `/structure/{decision_id}` | `paragraph_excerpt_chars` | `paragraph_excerpt_chars`: 50–5000 |
| GET | `/exam-question` | `topic`, `exclude_ids` | — |

`get_openapi()` selects the application or research schema route. These two discovery routes are implemented and tested separately but are not included in the saved contract.

### JSON request bodies

These fields are sent by the wrappers; required fields below are required Python arguments. The fixture does not validate body schemas.

- `/mock-decision`: `facts` (required), `question`, `deciding_court`, `preferred_language`, `statute_references`, `clarifications`, `fedlex_urls`, `limit`.
- `/attest`: `redacted_text`, `draft_text`, `audit_grounding`, `audit_quotes`, `client_redactor_version`, `client_redactor_summary`.
- `/verify-claim`: `claim` (required), `decision_id` (required), `pinpoint`.
- `/tool/{name}` receives the supplied argument object directly; inspect the tool’s current `inputSchema` first and do not wrap it in an `arguments` property.

## Scope and contract tests

This package provides HTTP wrappers, not the upstream CLI's local workflows. It has no CLI entry point, local packs, offline checks, or evidence-bundle implementation. Billing, quota, license-key, and admin wrappers are outside its scope. `call_tool()` accepts a tool name and arguments without local catalog/schema validation; available tools depend on the service.

`tests/opencaselaw/test_api_contract.py` compares GET wrapper requests with the saved fixture. Other client tests cover POST bodies, XML, schema retrieval, and error handling using mock transports. These tests detect client drift from the snapshot; they cannot detect upstream changes, verify live availability, or validate every response field. See [PLAN.md](../PLAN.md) for remaining validation work.
