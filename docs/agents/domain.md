# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo.

- Read `CONTEXT.md` at the repo root when it exists.
- Read `docs/internals/architecture.md` when architecture decisions touch the
  area being changed.
- If these files do not exist yet, proceed silently. `/domain-modeling` creates them lazily when terms or decisions are resolved.

## File structure

```text
/
├── CONTEXT.md
├── docs/internals/architecture.md
└── src/
```

## Use the glossary's vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term as defined in `CONTEXT.md`.

If the concept is not in the glossary yet, either reconsider the term or note the gap for `/domain-modeling`.

## Flag architecture conflicts

If output contradicts the existing architecture notes, surface the conflict
explicitly instead of silently overriding the decision.
