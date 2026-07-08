# Usage

## Basic Setup

```python
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator


class HelloHandler(RequestHandler):
    def get(self):
        self.write({"message": "hello"})


app = Application([(r"/hello", HelloHandler)])
Instrumentator().instrument(app).expose(app)
```

By default, `instrument(app)` wraps registered Tornado `RequestHandler` classes,
and `expose(app)` adds a Prometheus scrape endpoint at `/metrics`.

## Custom Metrics Endpoint

```python
Instrumentator().instrument(app).expose(app, endpoint="/internal/metrics")
```

## Gzip Metrics Output

```python
Instrumentator().instrument(app).expose(app, should_gzip=True)
```

The endpoint compresses output only when the request accepts gzip.

## Exclude Handlers

```python
Instrumentator(
    excluded_handlers=["/metrics", ".*admin.*"],
).instrument(app).expose(app)
```

Patterns are regular expressions matched against the normalized Tornado handler
pattern.

## Custom Metrics

```python
from prometheus_client import Counter

from prometheus_tornado_instrumentator import Instrumentator
from prometheus_tornado_instrumentator.metrics import Info


REQUESTS_BY_METHOD = Counter(
    "example_requests_by_method_total",
    "Example custom request counter.",
    ["method"],
)


def count_by_method(info: Info) -> None:
    REQUESTS_BY_METHOD.labels(info.method).inc()


Instrumentator().add(count_by_method).instrument(app).expose(app)
```

Instrumentation functions receive an `Info` object after a request finishes.

## Multiprocess Notes

Prometheus client multiprocess mode is supported through
`PROMETHEUS_MULTIPROC_DIR`. The directory must already exist.

```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
WORKERS=2 uv run python your_tornado_service.py
```

Clean the multiprocess directory before starting a new process group, following
the Prometheus Python client guidance.

## Current Scope

This package instruments Tornado HTTP `RequestHandler` routes. It does not try
to provide FastAPI, Starlette, ASGI mounted-app, or websocket route semantics.
