# Notes

- Packaging uses `uv_build` with `module-name = "opencaselaw"` because the distribution name (`opencaselaw-client`) differs from the import package. Tests deliberately avoid a source-path override so broken installations remain visible.
- This repository is a synchronous client library. Application deployment, database, telemetry, and agent-orchestration guidance in `AGENTS.md` does not imply those systems exist or need to be added here.
- Response models validate selected fields and preserve unknown fields in `raw`; direct model construction does not check application-error payloads. Client JSON wrappers perform that check before parsing models. Historical notebook outputs may show error payloads returned before this behavior changed.
- Slash-containing references need exact, unambiguous lookup before decision retrieval. Percent-encoding a slash preserves the request URL but cannot establish that an upstream route accepts it; local transport assertions alone cannot verify deployment routing.
- See [README.md](README.md#configuration) for configuration, timeout, and pacing behavior, and the [compatibility reference](docs/api-compatibility.md) for request contracts, error handling, citation validity, and verification limits. Saved responses and notebook outputs are historical examples, not service guarantees or maintained benchmarks.
