# Development

## Environment

Use `uv` for Python commands in this repository.

```bash
uv sync --extra dev
```

## Tests

```bash
uv run --extra dev python -m pytest -q
```

The current verified baseline is 105 passing tests.

## Coverage

Line coverage is a guardrail, not the main completion signal. Keep source line
coverage for `src/prometheus_tornado_instrumentator` at or above 98%, and keep
all upstream parity cases accounted for.

```bash
uv run --extra dev python -m pytest \
  --cov=prometheus_tornado_instrumentator \
  --cov-report=term-missing
```

## Package Build

```bash
uv build
uv run --extra dev python -m twine check dist/*
```

## Documentation Rules

- User-facing behavior belongs in `README.md`, `docs/usage.md`, and `docs/api.md`.
- Contributor workflow belongs in this file.
- Upstream migration evidence belongs under `docs/internals/porting/`.
- When upstream parity changes, update `docs/parity.md` and the relevant internal porting notes together.

