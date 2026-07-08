# Acceptance Criteria

This project ports the user-facing idea of `trallnag/prometheus-fastapi-instrumentator` to Tornado.

## Upstream test parity

The success bar includes test parity with the upstream source repository:

- The key completion indicator is: the Tornado port's full test suite passes.
- Every upstream test case must be accounted for.
- Every upstream behavior that has a Tornado equivalent must have a passing local behavior test.
- Framework-independent behavior should pass with equivalent assertions.
- FastAPI, Starlette, ASGI middleware, mounted-app, and router-specific tests must be ported to Tornado-equivalent behavior or explicitly marked as not applicable with a short reason.
- The Tornado port's full test suite must pass before the port is considered successful.

The goal is semantic parity, not running the upstream FastAPI test files unchanged. Unchanged upstream tests import and exercise FastAPI/Starlette behavior that this Tornado package intentionally does not provide.

## Coverage threshold

Line coverage is a guardrail, not the main completion signal.

- Do not require mechanical 100% line coverage.
- Require 100% accounting for upstream cases: each case is either ported to a Tornado-equivalent behavior test or explicitly marked not applicable.
- Keep source line coverage for `src/prometheus_tornado_instrumentator` at or above 98%.
- If coverage drops below 98%, either add meaningful tests or document why the uncovered branch is intentionally unreachable or framework-specific.

## Required first-version behavior

- `Instrumentator().instrument(app).expose(app)` instruments a Tornado application and exposes Prometheus output.
- Default metrics cover request count and request duration with low-cardinality labels.
- Custom instrumentation functions receive `Observation Info`.
- The metrics endpoint defaults to `/metrics`.
- Existing Tornado handlers do not need to inherit a special base class for first-version instrumentation.
