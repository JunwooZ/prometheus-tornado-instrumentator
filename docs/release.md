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

Pull requests and pushes to `main` run the full test matrix, coverage, and
package checks. See the [development guide](development.md) for local commands
and the conditions that warrant a local package build.

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

Use TestPyPI for:

- The first release workflow rollout.
- Changes to `release.yml`, `testpypi.yml`, or build configuration.
- Changes to package metadata, README rendering, package data, or source layout.
- Release candidates that should be install-tested before PyPI.

Use a unique pre-release version. Package indexes do not allow uploading the
same version twice.

Recommended sequence:

Replace `<pre-release-version>` before running the commands.

```bash
VERSION="<pre-release-version>"
git checkout -b "release/$VERSION"
# Update pyproject.toml and CHANGELOG.md.
git commit -m "chore: prepare $VERSION release"
git push origin "release/$VERSION"
```

Open a pull request, wait for CI, and merge it. Then tag the merged `main`
commit:

```bash
VERSION="<pre-release-version>"
git checkout main
git pull origin main
git tag "test-v$VERSION"
git push origin "test-v$VERSION"
```

After TestPyPI publishes, verify installation from TestPyPI:

```bash
VERSION="<pre-release-version>"
uv pip install \
  --index https://test.pypi.org/simple/ \
  --default-index https://pypi.org/simple/ \
  "prometheus-tornado-instrumentator==$VERSION"
```

Then verify a basic import and usage path in a clean environment.

## Production Release

Prepare the final version on a `release/*` branch:

Replace `<version>` before running the commands.

```bash
VERSION="<version>"
git checkout -b "release/$VERSION"
# Update pyproject.toml and CHANGELOG.md.
git commit -m "chore: prepare $VERSION release"
git push origin "release/$VERSION"
```

Record user-visible features, fixes, compatibility changes, and performance
changes under `## Unreleased` while developing. Test-only changes, refactors,
documentation maintenance, and CI changes normally do not belong there. During
release preparation, rename `Unreleased` to `<version> - <YYYY-MM-DD>` and add a
new empty `## Unreleased` section above it.

Open a pull request, wait for CI, and merge it into `main`.

### Pre-Tag Checklist

- [ ] The release pull request is merged into `main`, and all CI jobs passed.
- [ ] The local working tree is clean and `main` matches `origin/main`.
- [ ] `pyproject.toml` and the non-empty Changelog section use the same version.
- [ ] The version does not already exist on PyPI or as a local or remote tag.
- [ ] User-visible behavior changes are reflected in the relevant documentation.
- [ ] All release rehearsals required by the changed scope have passed.
- [ ] GitHub Actions shows no new deprecation or compatibility warnings.
- [ ] The `pypi` Environment will use normal approval without bypassing its rules.

Tag the merged `main` commit:

```bash
VERSION="<version>"
git checkout main
git pull origin main
git tag "v$VERSION"
git push origin "v$VERSION"
```

After the tag is pushed, `release.yml` automatically:

1. Confirm the tag version matches `pyproject.toml`, the tag commit is on `main`,
   and the matching Changelog section exists and is not empty.
2. Run tests.
3. Build the package with `uv build`.
4. Check the built files with `twine check dist/*`.
5. Publish to PyPI through Trusted Publishing.
6. Create a GitHub Release whose body is the matching Changelog section.

The GitHub Release includes the built wheel and source distribution as assets;
GitHub also provides source-code archives for the tag. The Release body contains
only the curated Changelog section for that version.

## Post-Release Checks

After the production workflow completes:

1. Confirm every `release.yml` job succeeded.
2. Confirm PyPI lists the expected final version.
3. Confirm the GitHub Release body matches the version's Changelog section and
   includes both the wheel and source distribution.
4. Install the exact version in a clean environment and verify a basic import.
5. Delete merged release branches locally and remotely. Keep `main`, release
   tags, and explicitly named backup branches.

## Release Smoke Test

When changing the GitHub Release automation, run **Release Smoke Test** manually
from `main` before the next production tag. It reuses the normal build and
package checks, creates a temporary `release-smoke-*` tag and draft GitHub
Release with the built distributions, verifies the draft and its two assets,
then removes both the draft and tag. It does not publish to TestPyPI or PyPI.

This checks the full GitHub Release portion of the workflow, including the
artifact download, tag verification, curated notes file, upload, and
permissions.

## Version Rules

- TestPyPI tags use `test-v<version>`.
- Production tags use `v<version>`.
- `pyproject.toml` versions do not use the leading `v`.
- The TestPyPI workflow must fail if `test-v${project.version}` does not match
  the pushed tag or its commit is not on `main`.
- The production workflow must fail if `v${project.version}` does not match the
  pushed tag, its commit is not on `main`, or if the project version is a
  pre-release.
- Never reuse a version number on PyPI or TestPyPI.
