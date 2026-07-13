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

Pull request CI always builds and checks the package. Run these commands locally
only when changing package configuration, metadata, README rendering,
`MANIFEST.in`, package data, or source layout, or when diagnosing a packaging
failure. Local build artifacts are never used for a production release.

```bash
uv build
uv run --extra dev python -m twine check dist/*
```

See [Release Process](release.md) for the full TestPyPI and PyPI publishing
workflow.

## Documentation Rules

- User-facing behavior belongs in `README.md`, `docs/usage.md`, and `docs/api.md`.
- Contributor workflow belongs in this file.
- Upstream migration evidence belongs under `docs/internals/porting/`.
- When upstream parity changes, update `docs/parity.md` and the relevant internal porting notes together.
- Do not hardcode the current test count in long-lived documentation. Historical
  baselines may keep a count when it is clearly labeled as a dated snapshot.
