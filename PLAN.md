# Follow-up review items

- Add CI for the supported Python range (at least 3.13 and 3.14), linting, tests, package builds, and dependency vulnerability scanning. There is currently no CI workflow. Verify and pin action SHAs before adding one; Dependabot configuration alone does not run these checks.
- Validate API contracts against an approved current OpenAPI snapshot or live service. This review used deterministic local transports only. Pydantic intentionally rejects malformed known fields; undocumented coercions previously accepted by dataclasses may expose upstream inconsistencies. Less stable endpoints still return dictionaries without deep schema validation.
- Review endpoint-specific bounds and enumerated inputs against that API contract. Most query/body parameters are still passed through to the server; this change validates configuration, timeout overrides, typed responses, and empty/dot path segments without guessing undocumented API limits.
