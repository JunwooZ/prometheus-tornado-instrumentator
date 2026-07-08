# Upstream Parity

This project is a Tornado semantic port inspired by
`trallnag/prometheus-fastapi-instrumentator`.

The goal is not to run the upstream FastAPI test files unchanged. Those tests
exercise FastAPI, Starlette, ASGI middleware, mounted-app routing, and websocket
features that this Tornado package intentionally does not provide.

Instead, every upstream behavior is handled in one of two ways:

- Ported to a Tornado-equivalent behavior test.
- Marked not applicable when the behavior is framework-specific and has no
  supported Tornado HTTP `RequestHandler` equivalent.

## Current Scope

Supported:

- `Instrumentator().instrument(app).expose(app)` for Tornado applications.
- Default request count, request size, response size, and latency metrics.
- Custom sync and async instrumentation functions.
- Custom Prometheus registries.
- Gzip metrics output.
- Regex handler exclusions.
- Dynamic routes added with `Application.add_handlers()`.
- Prometheus client multiprocess mode through `PROMETHEUS_MULTIPROC_DIR`.

Not supported:

- FastAPI or Starlette application objects.
- ASGI middleware integration.
- FastAPI mounted applications and included-router semantics.
- Websocket route instrumentation.
- Raw unmatched-path labels for requests that never enter a registered Tornado
  handler.

## Baseline

The initial upstream baseline is recorded in
[docs/internals/porting/upstream-baseline.md](internals/porting/upstream-baseline.md).
Detailed migration evidence is kept under `docs/internals/porting/`.

