# Upstream Baseline

This file records the upstream source used for the initial semantic-parity port.
It is intended for maintainers and agents that need to refresh parity later.

## Source

- Upstream repository: `trallnag/prometheus-fastapi-instrumentator`
- Upstream URL: https://github.com/trallnag/prometheus-fastapi-instrumentator
- Upstream license: ISC
- Baseline tag: `v8.0.2`
- Baseline tag SHA: `7c8519756bc492828f40e8530320894995a08200`
- Master SHA inspected during the initial audit: `c1c1fb645ce3b28d538413a9ac18cc7559c0c385`
- Audit date: 2026-07-08

## Local Verification

```bash
uv run --extra dev python -m pytest -q
```

Initial local baseline: 105 passing tests.

## Refresh Procedure

When updating the upstream baseline:

1. Record the new upstream tag or commit SHA.
2. Compare the upstream `tests/` directory against
   `docs/internals/porting/upstream-case-audit.md`.
3. Port framework-independent behavior to Tornado-equivalent tests.
4. Mark only framework-specific behavior as not applicable.
5. Update `docs/parity.md` when user-visible scope changes.
6. Run the full local test suite.

