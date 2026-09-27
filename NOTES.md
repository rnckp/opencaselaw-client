# Notes

- Packaging uses `uv_build` with `module-name = "opencaselaw"` because the distribution name (`opencaselaw-client`) differs from the import package. Tests deliberately avoid a source-path override so broken installations remain visible.
- The response models cover selected fields and preserve original payloads in `raw`. Unknown fields and HTTP-success error payloads can therefore survive parsing; model construction alone does not establish a successful lookup. The demo's saved `StG`/`ZH` response contains `error` and `candidates` rather than article text.
- This repository is a synchronous client library. Application deployment, database, telemetry, and agent-orchestration guidance in `AGENTS.md` does not imply those systems exist or need to be added here.
- See [README.md](README.md#configuration) for timeout and pacing behavior and [the compatibility reference](docs/api-compatibility.md) for contract evidence and its limits. Earlier timing observations are not maintained benchmarks or service guarantees.
