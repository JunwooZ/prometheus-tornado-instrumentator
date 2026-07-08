# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub issues for `git@github.com:JunwooZ/prometheus-tornado-instrumentator.git`. Use the `gh` CLI for issue operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`
- **Read an issue**: `gh issue view <number> --comments`, fetching labels as needed.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments`
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

When running inside a clone with the remote configured, infer the repo from `git remote -v`; `gh` does this automatically.

## Pull requests as a triage surface

**PRs as a request surface: no.**

`/triage` should process GitHub Issues only. External pull requests are not part of the request queue for this repo.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.
