# Release Process

This repository releases Python packages through GitHub Actions, `uv` builds,
Twine package checks, PyPI Trusted Publishing, and GitHub Releases.

The release flow is tag-driven. Normal code changes should enter `main` through
pull requests; publishing starts only when a release tag is pushed. TestPyPI
uses `test-v<version>` tags, while production PyPI uses `v<version>` tags. Both
publishing workflows reject tags whose commit is not already an ancestor of
`main`.

## Branch Model

- `main` is the stable branch and should receive changes through pull requests.
- `feature/*` branches are for new behavior.
- `fix/*` branches are for bug fixes.
- `release/*` branches are for version and changelog preparation.

Protect `main` in GitHub before relying on automated publishing:

- Require pull requests before merging.
- Require the CI workflow to pass before merging.
- Restrict direct pushes to `main`.
- Require approval for the `pypi` GitHub Environment.

## Continuous Integration

Pull requests and pushes to `main` should run the same checks maintainers run
locally:

```bash
uv sync --extra dev
uv run --extra dev python -m pytest -q
uv run --extra dev python -m pytest \
  --cov=prometheus_tornado_instrumentator \
  --cov-report=term-missing
uv build
uv run --extra dev python -m twine check dist/*
```

`uv build` creates the source distribution and wheel under `dist/`.
`twine check` validates the built distributions, including package metadata and
README rendering as PyPI will see them.

## Trusted Publishing Setup

Use PyPI Trusted Publishing instead of storing PyPI API tokens in GitHub
Secrets.

Create two GitHub Environments:

- `testpypi`
- `pypi`

Configure Trusted Publishers in PyPI and TestPyPI with these values:

| Index | Owner | Repository | Workflow filename | Environment |
| --- | --- | --- | --- | --- |
| TestPyPI | `JunwooZ` | `prometheus-tornado-instrumentator` | `testpypi.yml` | `testpypi` |
| PyPI | `JunwooZ` | `prometheus-tornado-instrumentator` | `release.yml` | `pypi` |

The publishing job must include:

```yaml
permissions:
  id-token: write
```

The release job also needs `contents: write` if it creates a GitHub Release.

## TestPyPI Pre-Release

Run a TestPyPI release before the first production release and whenever the
release workflow, package metadata, or build configuration changes.

Use a unique pre-release version. Package indexes do not allow uploading the
same version twice.

Examples:

- `0.1.1a1`
- `0.1.1rc1`
- `0.1.1.dev20260709`

Recommended sequence:

```bash
git checkout -b release/0.1.1a1
# Update pyproject.toml and CHANGELOG.md.
git commit -m "chore: prepare 0.1.1a1 release"
git push origin release/0.1.1a1
```

Open a pull request, wait for CI, and merge it. Then tag the merged `main`
commit:

```bash
git checkout main
git pull origin main
git tag test-v0.1.1a1
git push origin test-v0.1.1a1
```

After TestPyPI publishes, verify installation from TestPyPI:

```bash
uv pip install \
  --index https://test.pypi.org/simple/ \
  --default-index https://pypi.org/simple/ \
  prometheus-tornado-instrumentator==0.1.1a1
```

Then verify a basic import and usage path in a clean environment.

## Production Release

Prepare the final version on a `release/*` branch:

```bash
git checkout -b release/0.1.1
# Update pyproject.toml and CHANGELOG.md.
git commit -m "chore: prepare 0.1.1 release"
git push origin release/0.1.1
```

Open a pull request, wait for CI, and merge it into `main`.

Tag the merged `main` commit:

```bash
git checkout main
git pull origin main
git tag v0.1.1
git push origin v0.1.1
```

The `release.yml` workflow should:

1. Confirm the tag version matches `pyproject.toml` and the tag commit is on `main`.
2. Run tests.
3. Build the package with `uv build`.
4. Check the built files with `twine check dist/*`.
5. Publish to PyPI through Trusted Publishing.
6. Create a GitHub Release for the tag.

## Release Smoke Test

When changing the GitHub Release automation, run **Release Smoke Test** manually
from `main` before the next production tag. It reuses the normal build and
package checks, creates a temporary `release-smoke-*` tag and draft GitHub
Release with the built distributions, verifies the draft and its two assets,
then removes both the draft and tag. It does not publish to TestPyPI or PyPI.

This checks the full GitHub Release portion of the workflow, including the
artifact download, tag verification, generated notes, upload, and permissions.

## Version Rules

- TestPyPI tags use `test-v<version>`: `test-v0.1.1a1`.
- Production tags use `v<version>`: `v0.1.1`.
- `pyproject.toml` versions do not use the leading `v`: `0.1.1`.
- The TestPyPI workflow must fail if `test-v${project.version}` does not match
  the pushed tag or its commit is not on `main`.
- The production workflow must fail if `v${project.version}` does not match the
  pushed tag, its commit is not on `main`, or if the project version is a
  pre-release.
- Never reuse a version number on PyPI or TestPyPI.

## When To Use TestPyPI

Use TestPyPI for:

- The first release workflow rollout.
- Changes to `release.yml`, `testpypi.yml`, or build configuration.
- Changes to package metadata, README rendering, package data, or source layout.
- Release candidates that should be install-tested before PyPI.

For routine patch releases where the workflow and packaging configuration did
not change, CI plus the production release workflow is usually enough.
