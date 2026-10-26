# Engineering standard: roadmap

Every session that implements a stage should correct the specifications as
details change and say on its pull request what it corrected. It may change how
it delivers the stage when earlier work or implementation discoveries justify
that change. It should raise any change to the roadmap's stages, boundaries,
order or dependencies with the user instead of restructuring the roadmap itself.

## Stage 1: Required checks

Delivers the two checks that branch protection will require. `ci.yml` gains a
final job named "Required checks pass", after pipx: it runs `if: always()`,
needs every other job in the workflow, and fails unless each succeeded, using
`jq` over `toJSON(needs)`. A new workflow runs the dependency review action on
pull requests as a job named `dependency-review`, with the action pinned to a
commit and read-only permissions, as `docs.yml` does.

Proof: both checks appear on the stage's own pull request and pass.

Leaves branch protection to stage 4, and pinning the existing workflows to
stage 8. Every later stage that adds a job to `ci.yml` adds it to the gate's
`needs`.

Needs nothing.

## Stage 2: Ontology (interactive)

Delivers `docs/ontology.md`, written with the user, in the form the design's
Ontology section gives. It starts from the terms the design lists, and the
session adds or drops terms with the user. Each definition names the words it
replaces. The mkdocs nav section "Contribute" becomes "Development", and the
ontology goes there. `AGENTS.md` gains one line pointing to it.

Proof: the user accepts the ontology, and the strict mkdocs build passes.

Leaves every rename in code, documents, skills and issues to stage 14. Where the
ontology would rename something a user types or reads as a path (a command, a
flag, a configuration key or a generated file's path), the session records it in
the design as a named breaking change for the user to accept or refuse.

Needs nothing.

## Stage 3: Stories (interactive)

Delivers `docs/stories.md`, written with the user in the ontology's words, under
"Development", in the form the design's Stories section gives. It covers the
developer and the agent: happy paths, then user errors, then expected faults.
Among them it settles what `sync` says about files it skipped (#179), a
configuration uncoded cannot accept, a root configured outside the project
directory, `uvx` missing from `PATH`, a stale index, and how paths look on
Windows, including the paths `refs` prints and the paths in `sync`'s messages.

Proof: the user accepts the stories, the strict build passes, and every place a
story contradicts what uncoded does today is listed in the design as a named
behaviour change. The session sizes that list, and raises a split of stage 13
with the user if the list is too large to review as one pull request.

Leaves all code changes: Windows paths to stage 7, the rest to stage 13.

Needs stage 2.

## Stage 4: Repository admin (manual)

Delivers the repository settings the design names, changed by the user: turn on
Discussions and private vulnerability reporting; enable CodeQL default setup for
Python and Actions; confirm secret scanning and push protection; limit issues
and pull requests to collaborators; protect `main` with a required pull request,
the "Required checks pass" and `dependency-review` checks required, enforced for
admins, with "require branches to be up to date" and conversation resolution
left off; and give the `pypi` environment a deployment rule that allows only
tags matching `v*`, with no required reviewer.

Proof: an agent reads each setting back through `gh api` and finds it matches
the design. The user confirms the collaborators-only limit by eye.

Leaves `SECURITY.md`, the README's invitation and the Discussions link to
stage 10.

Needs stage 1.

## Stage 5: Standard and baseline

Delivers `docs/standard.md`, built from the design's Criteria section: each
criterion under its short title, with the full statement, a measure, a bar and a
check; the scope sentence; the exemplars; and the definition of done with its
titled questions. Delivers `docs/measurement.md`, holding the first measurement
of every criterion and saying how each number was taken, so the next measurement
can repeat it. Both go under "Development".

Proof: every criterion has a measured value, and every shortfall is owned by a
later stage of this roadmap. A shortfall no stage owns goes to the user, not
into a stage.

Leaves every gap to the stages that close it. The definition of done is not yet
asked of pull requests; stage 17 does that.

Needs stages 2 and 3, because true documents and few concepts are measured
against them.

## Stage 6: Compatibility and changelog

Delivers `docs/compatibility.md`, stating the design's Breaking changes rules in
words a user can act on, with `docs/upgrading.md` as its upgrade guide. Delivers
`docs/changelog.md`, in dreamcatcher's form, with an "Unreleased" section and
the Breaking, Added, Changed and Fixed headings. Its history is rebuilt briefly
from the GitHub releases: one entry for each release from 1.0.0 to 3.0.1,
linking the release; the two major releases link their upgrading sections; and
one line covers the 0.x releases. `[project.urls]` gains the Changelog link.
Both pages go under "Reference".

Proof: the strict build passes, and every release from 1.0.0 has an entry that
links its evidence.

Leaves the release checklist that maintains the changelog to stage 17.

Needs stage 5, so the baseline is measured before any gap closes.

## Stage 7: Platforms

Delivers the test matrix on Linux, macOS and Windows with Python 3.12 to 3.15,
with `fail-fast: false`, each job confirming it runs the interpreter it asked
for, and coverage combined across jobs into one 100% branch check, after nox.
Pre-commit runs on Windows as well as Linux. Delivers the Windows path behaviour
stage 3 decided. Adds a `--version` flag. The sdist holds `src` alone, and a
package job on each operating system builds the wheel from the sdist and runs
`uncoded --version`. Every new job's actions are pinned to commits, and every
new job joins the gate's `needs`. The `--version` flag and the Windows path
behaviour each get a changelog entry.

Proof: every job is green, and `uncoded check` passes on Windows.

Leaves pinning the existing jobs to stage 8, and test timeouts to stage 11.

Needs stage 3 for the Windows path decision, stage 6 for the changelog, and
stage 8, because both edit `ci.yml`.

## Stage 8: Workflows

Delivers the workflow half of the design's Infrastructure table: every action in
`ci.yml` and `publish.yml` pinned to a commit; read-only top-level permissions
with job-level grants; `persist-credentials: false` on every checkout;
`uv sync --locked`; a publish step that checks the tag matches the built
version, keeping the `pypi` environment and the attestations Trusted Publishing
makes by default; zizmor and actionlint in pre-commit, frozen to commits; and
`.github/dependabot.yml` for uv, pre-commit and GitHub Actions, grouped and with
a cooldown. This settles #223. `TY_VERSION` stays apart from the dev dependency,
as the design says.

Proof: zizmor and actionlint pass with no ignores, and CI is green. The stage
says that the tag check is first exercised at the next release.

Leaves the other hook revisions to stage 9.

Needs stage 1, because both edit `ci.yml`.

## Stage 9: Hooks

Delivers every pre-commit hook revision frozen to a commit, with a
`# frozen: vX` comment, and the rest of dreamcatcher's hooks that the design
lists: fix-byte-order-marker, check-illegal-windows-names, check-merge-conflict,
detect-private-key, the pygrep checks against blanket `noqa` and `type: ignore`,
a `pygrep` hook against U+00A0 and the zero-width and bidirectional characters,
and remark-validate-links over the Markdown outside `docs/`.

Proof: `pre-commit run --all-files` passes with every hook on, and each broken
link it found is fixed in the same pull request.

Leaves the hook that confines writes to `sync.py` to stage 11. A later stage
that adds a remote hook freezes it the same way.

Needs stage 8, because both edit `.pre-commit-config.yaml`.

## Stage 10: Shared, not supported

Delivers the design's "shared, not supported" list and the packaging metadata:
`.github/SECURITY.md`; the README inviting ideas, suggestions and questions to
Discussions, in dreamcatcher's words; `[project.urls]` with the documentation
site as Homepage, Repository and Discussions; the classifier
`Development Status :: 4 - Beta` with no `License ::` classifier; no
`src = ["src"]` under `[tool.ruff]`; validate-pyproject in pre-commit, frozen to
a commit; and `docs/contributing.md` deleted, with its "Edit the docs" and
"Change indexed content" sections moved into `AGENTS.md`.

Proof: validate-pyproject and the strict build pass, and `uv build` shows the
new metadata.

Leaves PyPI's copy of the metadata to the next release.

Needs stage 4 for the settings, and stage 9, because both edit
`.pre-commit-config.yaml`.

## Stage 11: Structure

Delivers:

- **No suppressions.** The `noqa` comments in `refs.py` and `tests/test_refs.py`
  become per-file ignores in `pyproject.toml`, each with its reason.
- **Machine-checked rules.** The empty-directory pruning in `skill.py` and
  `stubs.py` moves into `sync.py`. A `pygrep` hook confines file writes and
  removals to `sync.py`. An import-linter `layers` contract holds the three
  layers, and `docs/architecture.md` states them.
- **Loud failures.** pytest 9's `strict = true`, `pytest>=9.0`, and a per-test
  timeout from pytest-timeout, scaled for macOS and Windows in CI.
- `hypothesis` leaves the dev dependencies.

Proof: the suite and every hook pass on every platform, no `noqa` or
`type: ignore` remains, and `sync` prints exactly what it printed before.

Leaves keyword parameters to stage 12.

Needs stage 7, because the timeouts are scaled for its platforms, and stage 10,
because both edit `.pre-commit-config.yaml` and `pyproject.toml`. From here on
the stages run one at a time, since each edits `src` and `tests`.

## Stage 12: Keyword parameters

Delivers ruff's `too-many-positional-arguments` (PLR0917) with
`max-positional-args = 0`, and every function in `src` and `tests` changed to
keyword-only parameters, including test functions and fixtures, which take their
arguments after `*`. Every call site passes by name. Closes #219.

Proof: ruff passes with the rule on, the suite is green, and nothing a user sees
changes.

Leaves nothing.

Needs stage 11, because both edit `src` and `tests`. That also puts it after
stage 5's baseline.

## Stage 13: Behaviour

Delivers each behaviour change that stage 3 recorded in the design, apart from
Windows paths, each with tests and a changelog entry under "Unreleased". It also
checks that what every story says happens, including each exit status, is
covered by some test, at whatever grain suits the code, and adds tests where it
is not.

Proof: every change on the design's list has its tests and its entry, every
story's behaviour is covered by a test, and nothing else a user sees changes.

Leaves nothing, unless stage 3 split it.

Needs stage 3 for the stories and the list, stage 6 for the changelog, and stage
12, because both edit `src` and `tests`.

## Stage 14: Words

Delivers the consistency review against the ontology, and every rename it calls
for: code identifiers, documents, skill prose and open issues. It renames no
command, flag, configuration key or generated file path, unless stage 2 recorded
the rename in the design and the user accepted it. The skills are regenerated,
and their rewording gets a **Fixed** entry in the changelog.

Proof: the consistency review reports nothing, and no word the ontology replaces
remains outside the ontology's own list. Tests, hooks and the strict build pass.

Leaves the shape criteria to stage 15, and remeasuring the tracker to stage 17.

Needs stage 2 for the words, stage 6 for the changelog, and stage 13, because
both edit `src` and `tests`.

## Stage 15: Shape

Delivers:

- **No unused exports.** Every public name in `src` is imported by another
  module, or is `main` or `__version__`. Anything else becomes private.
- **One way.** The two directory walks in `config.py` become one (#234), along
  with any other duplicate the baseline found.
- **Rules not cases.** `docs/special-cases.md` starts, with every conditional
  that names a situation entered with its cause, and any whose cause is internal
  removed or generalised.
- **Symmetry.** `body` and `refs` (#205), any asymmetry the baseline records
  between the code and documentation index paths in `cli.py`, and the two
  navigation skills. Rewording a skill without changing its intent gets a
  **Fixed** changelog entry.

Proof: the four criteria meet their bars, measured the way the baseline measured
them, and #234 and #205 are closed. Nothing a user sees changes, apart from
skill wording with its **Fixed** entry. A change to which message or exit status
a user gets goes to the user, to be added to stage 3's list, not made here.

Leaves nothing.

Needs stage 5 for the measurements, stage 6 for the changelog, and stage 14,
because both edit `src` and `tests`.

## Stage 16: Accurate references

Delivers cog, as the design's accurate-references criterion describes: a block
under each command's heading in `docs/commands.md`, generated from its `--help`.
`docs/configuration.md` is not generated. `cog --check` runs in pre-commit on
one Python version with a fixed `COLUMNS`. Delivers `docs/testing.md` under
"Development", which closes #231, as the design's Testing page section
describes.

Proof: `cog --check` passes, and fails when a flag is renamed in the code alone.
The skills are reviewed against the commands and nothing is found.

Leaves nothing.

Needs stage 7, because `docs/testing.md` describes its CI and `--help` includes
`--version`, and stage 15, because both may edit `src`.

## Stage 17: Keep it there

Delivers the definition of done in `AGENTS.md`, with its titled questions,
asking every pull request to answer each under a "Definition of done" heading,
title first and with its evidence. Delivers `docs/releasing.md`, a checklist run
before each major or minor release: the consistency review; the triage of open
issues, including the ontology's replaced words; measuring every criterion;
adding new Python releases to the matrix; reading the repository settings back
through `gh api`, including the `pypi` environment's tag rule, and the
collaborators-only limit by eye; and moving the "Unreleased" entries under the
new version. The Releasing section of `AGENTS.md` moves there. Then it runs the
checklist once, triaging #226 and #162, and records the second measurement on
`docs/measurement.md`.

Proof: its own pull request answers the definition of done, the second
measurement is recorded, and every shortfall is closed or is an issue.

Leaves the next phase to plan from those issues.

Needs every earlier stage.
