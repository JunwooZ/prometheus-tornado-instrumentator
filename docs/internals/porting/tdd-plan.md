# TDD Plan

The port is complete only when the Tornado semantic-equivalent test suite passes. Work proceeds in slices that each add failing tests first, then the minimum implementation to make that slice pass.

## Slice 0: Project Skeleton

Goal: make the repository testable before porting behavior.

Status: complete, including PEP 561 `py.typed` package marker.

Tests to add:

- Package imports: `from prometheus_tornado_instrumentator import Instrumentator, metrics`
- Basic pytest smoke test

Implementation:

- `pyproject.toml`
- `src/prometheus_tornado_instrumentator/`
- `tests/`
- Dependencies: `tornado`, `prometheus-client`, `pytest`

Done when:

- `uv run --extra dev python -m pytest -q` runs and the smoke tests pass.

## Slice 1: Metric Closures

Goal: port framework-independent behavior from upstream `test_metrics.py`.

Status: complete. Label helpers, `Info`, request counter, latency, request size, response size, combined size, namespace/subsystem, custom labels, streaming-duration exclusion, duplicate collector handling, and default high-resolution latency filtering pass.

Upstream coverage:

- Label attribute construction
- Duplicate time series detection
- Request size
- Response size
- Combined size
- Latency
- Default metrics
- Request counter
- Custom labels
- Namespace and subsystem

Tests to port first:

- `_build_label_attribute_names`
- `_is_duplicated_time_series`
- `Info` / `Observation Info` attributes
- `latency`
- `requests`

Implementation:

- `metrics.py`
- `ObservationInfo`
- Tornado-shaped request/response test fixtures

Done when:

- The direct metric closure tests pass without needing a running Tornado server.

## Slice 2: Metrics Endpoint

Goal: expose Prometheus output from a Tornado app.

Status: complete for default path, custom path, content type, and gzip behavior.

Upstream coverage:

- `test_expose.py`
- `test_instrumentator_expose.py`
- gzip behavior from `test_instrumentation.py`

Tests to port first:

- Default `/metrics` endpoint returns 200
- Custom endpoint path returns 200
- Content type is valid and not duplicated
- Gzip is applied only when enabled and accepted

Implementation:

- `Instrumentator.expose(app, endpoint="/metrics", should_gzip=False)`
- Tornado `RequestHandler` for metrics output
- Custom `CollectorRegistry` support

Done when:

- Tornado app can expose metrics before request instrumentation exists.

## Slice 3: Handler Wrapper Basics

Goal: implement `Instrumentator().instrument(app)` using generated Tornado handler wrappers.

Status: complete. Basic handler wrapping, default upstream-style metrics, sync/async custom instrumentation, metric namespace/subsystem, env-var gating, custom metric names, bucket behavior, latency rounding, grouped and ungrouped status-code behavior, paths, and HTTP methods are passing.

Upstream coverage:

- Basic app instrumentation
- Default metric added when no explicit `add()` is used
- Custom instrumentation functions
- Request count and latency
- Status code grouping

Tests to port first:

- Basic GET handler increments request counter
- 404/500 status is observed
- Status grouping can be enabled/disabled
- Custom sync instrumentation receives `Observation Info`
- Custom async instrumentation receives `Observation Info`

Implementation:

- `Instrumentator.instrument(app)`
- Dynamic wrapper around registered `RequestHandler` classes in `middleware.py`
- `prepare()` / `on_finish()` observation lifecycle
- `add()` for sync and async instrumentation functions

Done when:

- A real Tornado request updates Prometheus metrics through the wrapper.

## Slice 4: Handler Representation and Exclusions

Goal: make labels stable and low-cardinality.

Status: complete for parameterized route patterns, exact and regex exclusions, `/metrics` exclusion, and unmatched-route non-recording policy.

Upstream coverage:

- Excluded handlers
- Regex exclusions
- Unmatched/untemplated route behavior
- Path parameters
- Starlette generic path tests ported to Tornado

Tests to port first:

- Handler label uses route pattern instead of raw path when possible
- Path parameters do not explode cardinality
- Excluded handlers are not instrumented
- `/metrics` can be excluded
- 404 behavior follows the documented policy

Implementation:

- Handler representation resolver in `routing.py`
- Excluded handler regex matching
- Unmatched route policy

Done when:

- Labels stay bounded for parameterized routes.

## Slice 5: Body and Streaming Semantics

Goal: match upstream body-capture semantics where Tornado allows it.

Status: complete. Default empty response body, `body_handlers` capture, empty body capture, small and large bulk body capture, small and large streaming body capture, first-write duration, runtime-error response accounting, and real response-size instrumentation are passing.

Upstream coverage:

- `test_middleware.py`
- Response size metrics
- Duration without streaming

Tests to port first:

- `info.response.body` is empty by default
- `body_handlers` enables body capture
- Small and large written responses are captured
- Streaming response capture is handled or explicitly documented
- Duration without streaming is less than full duration for streaming cases

Implementation:

- Wrapper overrides `write()` / `flush()` / `finish()` carefully
- Response body buffer only for configured handler patterns
- First-write timestamp

Done when:

- Response size/body tests pass or unsupported Tornado-specific cases are explicitly marked not applicable.

## Slice 6: Multiple Apps and Registries

Goal: keep metrics isolated across applications when requested.

Status: complete for custom registry isolation, default registry duplicate-safety, `metrics.default()`, and full metric set registration across multiple apps.

Upstream coverage:

- `test_instrumentator_multiple_apps.py`
- Custom `CollectorRegistry`
- Duplicate metric prevention

Tests to port first:

- Two Tornado apps with separate registries do not share custom metrics
- Multiple instrumented apps do not raise duplicate time series errors
- Full built-in metrics can be registered for more than one app

Implementation:

- Registry scoping in `Instrumentator`
- Duplicate-safe metric closure behavior

Done when:

- Multi-app tests pass in one pytest process.

## Slice 7: Environment and Multiprocess

Goal: match Prometheus client multiprocess behavior.

Status: complete for first-version parity. Invalid `PROMETHEUS_MULTIPROC_DIR`, metrics endpoint invalid-dir reporting, valid-dir scrape behavior, in-progress gauge behavior, parent-process multiprocess request counting, no duplicate output, and unsupported default-process metrics exclusion are covered.

Upstream coverage:

- `test_instrumentator_multiproc.py`
- Env-var validation
- Multiprocess scrape registry
- In-progress gauge
- Duplicate metric output prevention

Tests to port first:

- Invalid `PROMETHEUS_MULTIPROC_DIR` fails early
- Metrics endpoint handles invalid multiprocess dir
- Multiprocess count and duplicate-prevention tests
- In-progress gauge during concurrent requests

Implementation:

- Multiprocess registry handling in `Instrumentator` and metrics endpoint
- In-progress gauge in wrapper lifecycle

Done when:

- Env-gated multiprocess tests pass under the documented test command.

## Slice 8: Router and Mounted-App Accounting

Goal: close the remaining upstream parity matrix.

Status: complete for Tornado-equivalent dynamic `add_handlers`, multiple instrumentators on the same app, method-not-allowed behavior, route-pattern accounting, and documentation of FastAPI-only mounted/websocket/router-validation cases.

Upstream coverage:

- FastAPI included-router tests
- FastAPI mounted-app tests
- Websocket route accounting

Tests to port first:

- Tornado `add_handlers` routes are instrumented
- Multiple instrumentators on one Tornado app observe both existing and late-added handlers
- Host/prefix patterns are represented correctly where supported
- Method-not-allowed and not-found behavior is covered

Implementation:

- Additional route traversal/wrapping logic in `routing.py`
- Not-applicable notes for FastAPI-only validation/router features

Done when:

- Every upstream router/mounted-app test is either represented by a passing Tornado test or explicitly marked not applicable in `docs/internals/porting/upstream-test-parity.md` and `docs/internals/porting/upstream-case-audit.md`.

## Current Verification

`uv run --extra dev python -m pytest -q` passes with 105 tests.

Source line coverage for `src/prometheus_tornado_instrumentator` should stay at
or above 98%. The project does not require mechanical 100% line coverage; the
stricter requirement is that every upstream case is accounted for as either a
ported Tornado-equivalent behavior or a documented not-applicable framework
case.

## Working Rule

After each slice:

- Run the slice tests.
- Run the full available suite.
- Update `docs/parity.md` and `docs/internals/porting/upstream-test-parity.md` if a parity decision changes.
- Do not move to the next slice with failing tests unless the failure is deliberately carried as the next red test.
