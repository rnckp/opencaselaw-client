# Contributing

Keep changes focused, preserve public contracts, and validate behavior with offline tests where
possible. See [AGENTS.md](AGENTS.md) for repository policies and [PLAN.md](PLAN.md) for open tasks.

## Setup and checks

Requires Python 3.12 or newer and `uv`. From the repository root:

```bash
uv sync
uv run pre-commit install
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run pre-commit run --all-files
uv build --force-pep517
```

Use `uv run ruff format .` to apply formatting. The package uses `uv_build`; `--force-pep517` builds
with the declared backend even when the installed uv CLI bundles a newer backend. Run `uv sync`
after dependency or build-metadata changes. Do not override `PYTHONPATH` to work around an
installation problem.

## Project layout

Source lives in `src/opencaselaw/`, with package tests in `tests/opencaselaw/`. `client.py` handles
HTTP and endpoint wrappers, `config.py` validates settings, and `models.py` validates selected
response shapes.

The distribution is `opencaselaw-client`; the import package is `opencaselaw`. See the [client
guide](docs/client-guide.md) for public behavior and [NOTES.md](NOTES.md) for implementation
rationale.

## Examples

Launch [the notebook](examples/opencaselaw_demo.ipynb) with `uv run jupyter lab` after `uv sync`.
Use the repository environment as the kernel. API cells make live requests, and the kernel's working
directory controls implicit configuration and relative output paths.

## Tests and API verification

The default test suite makes no network requests. To explicitly run read-only live checks:

```bash
uv run pytest --live-api tests/opencaselaw/test_live_api.py
```

These checks contact the service and may fail because of availability or upstream changes. They
cover representative behavior, not every endpoint or complete data coverage. See the [API
compatibility notes](docs/api-compatibility.md) for evidence limits. CI runs live checks only when
enabled through manual workflow dispatch.

## Local hooks

Hooks run the locked Ruff version with safe fixes and formatting on staged Python files and
notebooks. File checks cover YAML/JSON, conflict markers, private keys, whitespace, and newly added
files over 1 MB. Gitleaks scans staged changes for credentials. The first hook run downloads
reusable environments. Run `uv sync` first because Ruff hooks use `--no-sync`; review and stage
fixes before committing again.

## CI and dependency checks

`Quality` runs hooks and offline tests, builds distributions, and performs an installed-wheel import/resource
check on Python 3.12. `Python 3.13` and `Python 3.14` run compatibility tests without repeating lint
or builds. Jobs use cached uv environments, read-only permissions, ten-minute timeouts, and
cancellation of superseded runs.

Gitleaks is skipped in CI because its hook scans staged changes. Verify GitHub secret scanning and
push protection for remote commits. Dependabot monitors uv, GitHub Actions, and external hooks
weekly, groups routine updates, and applies a seven-day cooldown. Preserve uv's seven-day
package-resolution cooldown.

A separate dependency audit runs for dependency changes, weekly, or manually. To run it locally
(contacts external package and advisory services):

```bash
uv audit --locked --preview-features audit-command
```

## Pull requests

Use a short-lived `feat/`, `fix/`, or `refactor/` branch and a focused PR into `main`. Use
conventional commit messages. Verify hosted CI and configure branch protection to require `Quality`,
`Python 3.13`, and `Python 3.14`. The path-filtered dependency audit should not be a required status
check. Local checks do not establish hosted workflow or branch-protection status.
