# Open tasks

Unresolved implementation, compatibility, and infrastructure work. See
[NOTES.md](NOTES.md) for established constraints and historical evidence.

- Exhaustive response validation and live POST verification remain open; see the [compatibility reference](docs/api-compatibility.md#evidence-and-verification-limits) for the schema comparison and representative live read coverage. Future live checks require authorization under `AGENTS.md`.
- Verify hosted CI, Dependabot, secret scanning/push protection, and branch protection after pushing. Require `Quality`, `Python 3.13`, and `Python 3.14` on `main`; the path-filtered dependency audit should not be required.
