# OpenCaseLaw Python Client

An independent, synchronous Python client for Swiss legal research through the public, no-key
[OpenCaseLaw](https://opencaselaw.ch) REST API.

This project is unofficial and is not affiliated with OpenCaseLaw.

The service's [official API documentation](https://opencaselaw.ch/api) is the reference for the
upstream API. This repository documents the client behavior and the limits of its local checks.

## Installation

Requires Python 3.12 or newer and `uv`. From a local checkout, install the package and its declared
development dependencies:

```bash
cd opencaselaw-client
uv sync
```

## Quick start

Save this example in a Python file and run it with `uv run <file>.py` from the repository root. It
makes live requests.

```python
from opencaselaw import OpenCaseLawClient

with OpenCaseLawClient() as client:
    results = client.search_decisions(query="Mietrecht Kündigung", language="de", limit=5)
    for decision in results.results:
        print(decision.citation_string_de, decision.canonical_url)

    if results.results:
        decision = client.get_decision(results.results[0].decision_id)
        print(decision.title)
```

For more examples, see the [client guide](docs/client-guide.md) and [example
notebook](examples/opencaselaw_demo.ipynb). Notebook API cells also make live requests; response
examples do not guarantee current service availability.

## Usage

Use a context manager or call `close()` to release the HTTP client. Instances are intended for
sequential use, with request spacing per instance. HTTP and transport errors propagate to callers.

The client covers decisions, lookup, courts, statistics, scholarship, citations, laws, legislation,
commentaries, research helpers, exports, and Atom feeds. The [API compatibility
notes](docs/api-compatibility.md) list the saved public request contract and schema-discovery
routes. Billing, quota, license-key, and private/admin wrappers are outside the package's scope.

Pagination is caller-managed. Inspect continuation and uncertainty metadata before treating a search
as complete. API error payloads raise `OpenCaseLawAPIError`; tool errors raise
`OpenCaseLawToolError`. Citation resolution does not establish pinpoint validity. Coverage reported
by `list_courts()`, `get_statistics()`, and `get_scraper_health()` comes from the service.

See the [client guide](docs/client-guide.md) for method examples, response behavior, and error
handling.

## Configuration

Automatic configuration reads the `opencaselaw:` section of `config.yaml` in the working directory.
Use `auto_discover_config=False` to disable that lookup. An explicit `config_path` accepts either a
section or flat settings. The defaults are a 30-second HTTPX timeout, a 0.2-second interval between
request starts, and `default_limit=10`. Constructor settings override configured values. Selected
methods accept `request_timeout`; retries are not automatic.

See [configuration details](docs/client-guide.md#configuration) for validation, overrides, and
file-discovery behavior. The checkout includes [config.yaml](config.yaml); the working directory
controls implicit configuration and relative output paths.

## Scope and compatibility

This is a client library. It does not provide an application server or async client. Local tests use
offline fixtures or synthetic responses. They check the implemented contracts without establishing
current upstream availability or complete data coverage.

See the [API compatibility notes](docs/api-compatibility.md) for evidence and verification limits,
[NOTES.md](NOTES.md) for implementation decisions and historical observations, and
[PLAN.md](PLAN.md) for open tasks.

## Development

Run the local checks from the repository root:

```bash
make check
```

The [Makefile](Makefile) also provides `sync`, `format`, `lint`, `test`, `test-live`, and `build`.
Running `make` defaults to `check`; `test-live` explicitly contacts the public API.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, hooks, builds, CI, and optional checks. Agent
guidance is in [AGENTS.md](AGENTS.md).

## Responsible use

Keep request rates modest, retain source attribution and applicable reuse terms, and avoid sending
confidential or personal data to public endpoints. Consider contributing or donating to
[OpenCaseLaw](https://opencaselaw.ch).

## License

This client code is licensed under the [MIT License](LICENSE). The license does not cover data, API
content, or other source materials returned by the service. Consult
[OpenCaseLaw](https://opencaselaw.ch) and the original sources for their reuse terms.
