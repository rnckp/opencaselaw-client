# Public API compatibility audit

Checked on 2026-09-27 against the deployed [application schema](https://mcp.opencaselaw.ch/api/openapi.json), [typed research subset](https://mcp.opencaselaw.ch/api/research/openapi.json), and [tool catalog](https://mcp.opencaselaw.ch/api/tool). The [official Python client](https://github.com/jonashertner/opencaselaw/tree/05a6dcd1f7c24ba4091d8ae254dc7975e1589db6/clients/python) and server source were reviewed at commit `05a6dcd1f7c24ba4091d8ae254dc7975e1589db6`.

The deployed schema governs the HTTP wrappers. The website lists mock decisions as GET, but the deployed schema and official route implementation use POST. The typed research schema is deployed and reachable; its availability notice on the website lags that deployment.

## Changes and compatibility

- Added docket lookup, eight scholarship routes, tool discovery/calls, cantonal law paths, and federal article XML. `get_openapi()` also retrieves either schema.
- Added search aliases (`q`), publication filtering, pinpoint control, citation offset, commentary canton, and Botschaft publication-year bounds.
- Corrected relevant-Erwägung requests to send `top_k`. `max_paragraphs` remains a Python alias, with conflicting values rejected.
- The server rejects `decision_type` and `legal_area` search filters. The existing Python `decision_type` parameter now raises locally. Use query terms or supported court/chamber filters.
- Search models expose continuation, lower-bound, degraded-ranking, and query-condensation metadata. Missing metadata from older servers stays unknown (`None`). No automatic exhaustive-search claim or pagination is inferred.
- Law article text can be absent, null, or empty; `articles` can be null. This is valid in the typed contract. Callers should inspect `text_status` and handle `articles or []`.
- Tool failures marked `_is_error: true` raise `OpenCaseLawToolError`; its payload remains available for inspection. Other dictionary-returning routes retain their complete server payloads, including error/coverage/attribution fields.

## Endpoint inventory

All paths below are relative to `https://mcp.opencaselaw.ch/api`. Path parameters appear in braces. Query parameter limits are server contracts; this client generally leaves endpoint-specific validation to the server. The client uses its configured `default_limit` (10 unless changed) when a wrapper limit is omitted, rather than reproducing each server default.

| Method | Path | Query parameters | Numeric bounds |
| --- | --- | --- | --- |
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

### JSON request bodies

- `/mock-decision`: `facts` (required), `question`, `deciding_court`, `preferred_language`, `statute_references`, `clarifications`, `fedlex_urls`, `limit`.
- `/attest`: `redacted_text`, `draft_text`, `audit_grounding`, `audit_quotes`, `client_redactor_version`, `client_redactor_summary`.
- `/verify-claim`: `claim` (required), `decision_id` (required), `pinpoint`.
- `/tool/{name}` takes the argument object described by that tool’s current `inputSchema`; do not wrap it in an `arguments` property.

## Official CLI versus REST

The [CLI guide](https://opencaselaw.ch/cli/) and [research manual](https://github.com/jonashertner/opencaselaw/blob/05a6dcd1f7c24ba4091d8ae254dc7975e1589db6/docs/research-cli.md) include local packs, draft/quotation checks, identity resolution, and evidence bundles. These are composed CLI workflows, not dedicated REST endpoints. They are not reimplemented here. The HTTP tool bridge exposes additional research capabilities, including administrative practice; the notebook demonstrates schema discovery before an optional call.

Billing, quota, license-key and admin operations remain outside this public research client. No live decision, scholarship, document-processing or tool-execution calls were made during this audit; only documentation/schema/catalog endpoints were fetched. Service availability, latency and populated result bodies were not end-to-end verified.

The compact request-contract fixture in `tests/fixtures/public_api_contract.json` records the deployed schema URL, retrieval date and SHA-256. It is intentionally versioned to detect unsupported route/parameter changes without network-dependent tests.
