# Documentation

## User Docs

- [Usage](usage.md): install, run, configure, and expose metrics.
- [API reference](api.md): public imports, `Instrumentator`, `Info`, and built-in metrics.
- [Upstream parity](parity.md): supported Tornado scope and framework-specific exclusions.

## Maintainer Docs

- [Development](development.md): `uv`, tests, coverage, and build checks.
- [Release process](release.md): branch model, TestPyPI, PyPI Trusted
  Publishing, and tag-driven GitHub Releases.
- [Architecture](internals/architecture.md): Tornado handler-wrapper design.
- [Upstream baseline](internals/porting/upstream-baseline.md): source version used for the initial port.

## Internal Porting Evidence

These files preserve the migration audit trail. They are useful for maintainers
and agents, but they are not part of the main user path.

- [Acceptance criteria](internals/porting/acceptance.md)
- [TDD plan](internals/porting/tdd-plan.md)
- [Upstream test parity matrix](internals/porting/upstream-test-parity.md)
- [Upstream case audit](internals/porting/upstream-case-audit.md)
