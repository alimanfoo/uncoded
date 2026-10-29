# Releasing

The maintainer decides when to release. This page lists what to do before, when
and after publishing a release. The package takes its version from the Git tag,
so creating the tag is the only version change.

## Choose the version

Choose the version from the headings of the entries under **Unreleased** in
[the changelog](changelog.md), which says what kind of release each heading
makes.

## Check the standard

If the release is major or minor, do this. A patch release skips it.

1. Run the consistency review, as the method on
   [the measurement](measurement.md) says. Fix what is quick to fix, and file an
   issue for each other finding.
2. Triage the open issues against the measure of
   [Accurate tracker](standard.md#accurate-tracker). Rewrite or close each issue
   that falls short, and say why.
3. Measure every criterion in [the standard](standard.md), by the method that
   [the measurement](measurement.md) gives, reading the enduring documents
   against the code. Replace the measurement with the results, and name an issue
   for each shortfall that a change to the repository can fix, filing one where
   no open issue owns it.

A shortfall does not hold the release back. A failing test or check does.

## Check what nothing else checks

If the release is major or minor, do this too. A patch release skips it.

1. Add each Python release that came out since the previous release to the
   `python` list of the `test` job in `.github/workflows/ci.yml`. That list runs
   from the `requires-python` floor in `pyproject.toml` up, and is the one
   record of the Python versions that uncoded is tested on.
2. Read the repository settings back, since they live outside the repository.
   The calls need a `gh` session with admin rights on the repository:

   ```sh
   R=repos/alimanfoo/uncoded
   gh api $R --jq '{has_discussions, security_and_analysis, pull_request_creation_policy}'
   gh api $R/private-vulnerability-reporting
   gh api $R/code-scanning/default-setup --jq '{state, languages}'
   gh api $R/dependency-graph/sbom --jq '.sbom.name'
   gh api $R/branches/main/protection
   gh api $R/environments/pypi
   gh api $R/environments/pypi/deployment-branch-policies
   ```

   Check that Discussions, private vulnerability reporting, secret scanning and
   push protection are on, that the dependency graph is on, which the SBOM call
   shows by returning the repository's name, that CodeQL default setup covers
   `actions` and `python`, and that only collaborators can open pull requests.
   Check that `main` requires a pull request and the "Required checks pass" and
   `dependency-review` checks, enforced for admins, with "require branches to be
   up to date" and conversation resolution off. Check that the `pypi`
   environment allows only tags that match `v*`, and has no required reviewer.
   Then check by eye, in the repository's settings on GitHub, that only
   collaborators can open issues, since the API does not report it. Correct any
   setting that differs.

## Prepare the release

1. Move the entries under **Unreleased** into a section for the new version,
   headed like the released sections below it. Keep each entry under its
   heading, and leave out a heading with no entries.
2. If the release is major, add a section to [Upgrading](upgrading.md) that
   takes a project from the previous major version, and link it from the top of
   the version's section in the changelog, as 3.0.0 does.
3. Merge these changes, and the measurement if the release has one, in one pull
   request. Then wait for CI to pass on `main`.

## Publish

Create and publish a GitHub release from `main`. Name the tag `v` followed by
the version, such as `v3.0.1`:

```sh
gh release create v3.0.1 --target main --generate-notes
```

Publishing the release starts `.github/workflows/publish.yml`. It builds the
source distribution and wheel from the tag, then uploads them to
[PyPI](https://pypi.org/p/uncoded). The build fails before the upload if the tag
did not build that version. Watch the workflow until it ends:

```sh
gh run watch --exit-status "$(gh run list --workflow publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

The upload uses PyPI Trusted Publishing, so it needs no `PYPI_TOKEN` or any
other long-lived publishing secret. The PyPI trusted publisher is configured
for:

- PyPI project: `uncoded`
- Owner: `alimanfoo`
- Repository: `uncoded`
- Workflow: `publish.yml`
- Environment: `pypi`
