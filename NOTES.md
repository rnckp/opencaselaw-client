# Notes

- OpenCaseLaw's OpenAPI document describes many public responses with untyped `{}` schemas. The client therefore models stable high-use shapes conservatively and preserves unknown fields in `raw` rather than guessing deep response schemas from live examples.
- The live `/courts` endpoint may return a top-level JSON array, not an object. Keep `list_courts()` tolerant of both shapes and use `list_court_models()` when parsed court items are needed.
- `search_decisions()` local overhead is negligible compared with the public API response time. A compact 5-result live `/decisions` search took ~2.6-3.7s in HTTP request time, while JSON decoding and model conversion were each ~0.0001s.
- A broad live `/decisions` search for `Bundesgericht` with `limit=3` took ~11s on 2026-05-23. Use `search_decisions(..., request_timeout=60.0)` in notebooks or demos where transient API slowness would otherwise trip the 30s default.
- The live `/mock-decision` research helper can exceed the general 30s client timeout. Use `mock_decision(..., request_timeout=120.0)` in examples or interactive notebooks instead of raising the global default for all endpoints.
