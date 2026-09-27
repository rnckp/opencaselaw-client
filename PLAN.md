# Follow-up review items

- Add CI for the supported Python range (at least 3.13 and 3.14), linting, tests, package builds, and dependency vulnerability scanning. There is currently no CI workflow. Verify and pin action SHAs before adding one; Dependabot configuration alone does not run these checks.
- The 2026-09-27 API audit now covers deployed OpenAPI parameters, the typed research subset, tool discovery, and official source. Remaining validation: opt-in live research smoke tests for service availability, latency, and populated payloads. Tests use local transports; less stable endpoints retain dictionaries without deep schema validation.
- Endpoint-specific numeric bounds are recorded in `docs/api-compatibility.md`; most query/body value validation remains server-side. Revisit local validation only where it improves error reporting without duplicating evolving server rules.
