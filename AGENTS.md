# Project Instructions

## Agent skills

### Issue tracker

Issues and PRDs live in GitHub Issues for `git@github.com:JunwooZ/prometheus-tornado-instrumentator.git`; external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: use root `CONTEXT.md` and `docs/internals/architecture.md`.
See `docs/agents/domain.md`.

For upstream parity updates, read
`docs/internals/porting/upstream-baseline.md` before changing tests or parity
docs.

## Python workflow

Use `uv` for Python-related commands in this repository. Run tests and Python
entry points through `uv run`, and manage Python dependencies with `uv` rather
than direct `python`, `pip`, or bare `pytest` commands.

## Git commit format

Use Conventional Commits for this repository:

```text
<type>(<scope>): <summary>
```

Use an English imperative summary. Omit `scope` when it does not add clarity.
Common types are `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`,
`perf`, `style`, and `build`.
