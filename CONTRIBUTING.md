# Contributing

Thanks for taking the time to improve this project.

## Development Setup

```bash
uv sync --extra dev
```

## Test

```bash
uv run --extra dev python -m pytest -q
```

## Build Check

```bash
uv build
uv run --extra dev python -m twine check dist/*
```

See [docs/release.md](docs/release.md) for the full TestPyPI, PyPI Trusted
Publishing, and GitHub Release workflow.

## Commit Messages

Use Conventional Commits:

```text
<type>(<scope>): <summary>
```

Examples:

```text
docs(api): document public metric closures
fix(metrics): avoid duplicate collectors
chore(package): add PyPI metadata
```

Use an English imperative summary. Omit `scope` when it does not add clarity.

## Upstream Parity Changes

When changing behavior inherited from the upstream FastAPI instrumentator idea,
read [docs/parity.md](docs/parity.md) and
[docs/internals/porting/upstream-baseline.md](docs/internals/porting/upstream-baseline.md)
first.
