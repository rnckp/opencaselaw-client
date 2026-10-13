# Follow-up review items

- Evaluate broader response-schema validation and additional opt-in endpoint smoke checks if upstream schemas expand. Current live checks cover representative read-only operations; POST execution remains unverified.
- GitHub dependency review checks vulnerabilities introduced by pull-request dependency changes. A full installed-environment vulnerability scan remains deferred; the user declined adding `pip-audit` for this change.
- Resolve hook setup before requiring it: `pre-commit` is neither a declared dependency nor configured in this repository. Adding it requires dependency approval under `AGENTS.md`.
