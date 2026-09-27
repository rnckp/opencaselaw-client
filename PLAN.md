# Follow-up review items

- Add CI for the declared Python range (starting with 3.13 and 3.14), linting, tests, package builds, and dependency vulnerability scanning. There is currently no CI workflow. Verify and pin action SHAs before adding one; Dependabot configuration alone does not run these checks.
- Add opt-in live smoke tests for service availability and populated responses. Existing tests use local transports; saved notebook outputs are historical examples. See [the compatibility reference](docs/api-compatibility.md#evidence-and-verification-limits) for evidence gaps, including response and POST body schemas.
- Resolve hook setup before requiring it: `pre-commit` is neither a declared dependency nor configured in this repository. Adding it requires dependency approval under `AGENTS.md`.
