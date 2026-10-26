# Implementation notes

Durable decisions, constraints, and historical observations. Public usage is in
the [client guide](docs/client-guide.md); open work is in [PLAN.md](PLAN.md).

- Required CI covers Python 3.12–3.14. A local Python 3.15 smoke test passed on macOS arm64 on 2026-10-14, but the locked `pydantic-core` needed a source build. Keep 3.15 outside required CI until eligible wheels make setup fast and reproducible; a local pass does not establish Linux compatibility.

- Packaging uses `uv_build` with `module-name = "opencaselaw"` because the distribution name (`opencaselaw-client`) differs from the import package. Tests deliberately avoid a source-path override so broken installations remain visible.
- This repository is a synchronous client library. Application deployment, database, telemetry, and agent-orchestration guidance in `AGENTS.md` does not imply those systems exist or need to be added here.
- Response models validate selected fields and preserve unknown fields in `raw`; direct model construction does not check application-error payloads. Client JSON wrappers perform that check before parsing models. Historical notebook outputs may show error payloads returned before this behavior changed.
- Slash-containing references need exact, unambiguous lookup before decision retrieval. Percent-encoding a slash preserves the request URL but cannot establish that an upstream route accepts it; local transport assertions alone cannot verify deployment routing.
- The 2026-10-23 deployed schemas add publication-date filters and materials document types without new routes. Publication queries may restrict decision dates (`publication_window_decided_from`); `doc_type` on the curated `/materialien` search is explicitly a no-op. Keep these limits visible to callers rather than implying complete or filtered results.
- See [README.md](README.md#configuration) for configuration, timeout, and pacing behavior, and the [compatibility reference](docs/api-compatibility.md) for request contracts, error handling, citation validity, and verification limits. Saved responses and notebook outputs are historical examples, not service guarantees or maintained benchmarks.

## eMudhra/emSign patch, 2026-10-26

The affected certifi lock and environment now require at least 2026.10.19. Newer secure versions were preserved. Keep the existing seven-day cooldown. Remove only the incident package exemptions after certifi artifacts age seven days (2026-10-27 after 03:24:17 CET). Retain the security minimums. See the workspace SECURITY-PATCH-2026-10-26.md report for verification and scope.
