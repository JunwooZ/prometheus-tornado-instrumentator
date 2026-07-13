# Prometheus Tornado Instrumentator

A Tornado-focused Prometheus instrumentation library inspired by
[`trallnag/prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator).

The goal is to provide a Tornado-native user experience:

```python
from prometheus_tornado_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## Installation

From PyPI:

```bash
pip install prometheus-tornado-instrumentator
```

From a local checkout:

```bash
uv pip install -e .
```

## Quick Start

```python
from tornado.web import Application, RequestHandler

from prometheus_tornado_instrumentator import Instrumentator


class HelloHandler(RequestHandler):
    def get(self):
        self.write({"message": "hello"})


app = Application([(r"/hello", HelloHandler)])
Instrumentator().instrument(app).expose(app)
```

This instruments registered Tornado handlers and exposes Prometheus scrape output
at `/metrics` by default.

## Features

- Default Prometheus metrics for request count, request size, response size, and latency.
- Custom sync or async instrumentation functions.
- Custom metric namespace and subsystem.
- Custom Prometheus `CollectorRegistry`.
- Gzip support for metrics output.
- Regex-based handler exclusions.
- Dynamic route instrumentation for handlers added with `Application.add_handlers()`.
- Prometheus client multiprocess support through `PROMETHEUS_MULTIPROC_DIR`.

## Scope

This package instruments Tornado HTTP `RequestHandler` routes.

It does not provide FastAPI, Starlette, ASGI mounted-app, included-router, or
websocket route semantics. See [docs/parity.md](docs/parity.md) for the upstream
semantic-parity notes.

## Documentation

- [Usage](docs/usage.md)
- [API reference](docs/api.md)
- [Development](docs/development.md)
- [Release process](docs/release.md)
- [Upstream parity](docs/parity.md)
- [Documentation index](docs/README.md)

## Development

Use `uv` for local development:

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -q
```

## License

This project is licensed under the ISC License. See [LICENSE](LICENSE).

This project is inspired by
[`trallnag/prometheus-fastapi-instrumentator`](https://github.com/trallnag/prometheus-fastapi-instrumentator),
which is also licensed under the ISC License. See [NOTICE](NOTICE) for the
initial upstream baseline.
