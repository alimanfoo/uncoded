# Engineering standard: design

This design develops the [requirements](requirements.md) into the decisions that
`docs/standard.md` will record.

## Exemplars

The standard keeps dreamcatcher's five exemplars and adds these. Each is
credited only with what reading it verified on 2026-10-25.

- **urllib3** for the supply chain and releases. Every action is pinned to a
  commit, every workflow sets read-only `permissions`, zizmor runs in
  pre-commit, CodeQL covers `actions`, Scorecard runs, Dependabot groups its
  updates with a cooldown, publishing goes through a protected environment with
  `attestations: true`, and `SECURITY.md` gives a private reporting route.
- **nox** for cross-platform testing. CI runs Linux, macOS and Windows across
  Python versions with `fail-fast: false`, combines coverage from every platform
  and requires 100% (`noxfile.py`), isolates platform branches behind a
  patchable `_PLATFORM`, and runs pytest with strict markers, strict config and
  `xfail_strict`.
- **pipx**, second to nox, for testing the installed wheel and for test timeouts
  scaled by platform. Its "Required checks pass" job runs `if: always()`, needs
  every other job, and fails unless each succeeded.
- **llm** for a command reference generated from the code. CI fails when
  `docs/help.md` no longer matches the command's `--help` output.
- **uv and ruff** for what counts as a breaking change. uv separates public
  formats from internal ones and scales care to "expected real-world impact".
  Ruff counts a change as breaking when "the intent of the rule changes", and
  deprecates before it removes.

## Breaking changes

The package version is the only version. This refines the requirement's
definition of a breaking change, following uv and ruff.

A change is **breaking**, and needs a major release, when it:

- removes or renames a command, a flag, a configuration key or an artefact path,
  or changes its meaning or default;
- changes an exit status, or the format of the data a command writes to standard
  output;
- changes an artefact's layout rules, such as how keys nest or which keys end in
  `/`, as opposed to which symbols or headings it lists;
- changes the intent of a skill, by removing, reversing or narrowing an
  instruction or reordering a workflow step; or
- drops support for a Python version.

A change is a **minor** release when it adds a command, flag, configuration key,
artefact or skill guidance, or deprecates something with a warning. Removing a
deprecated feature is breaking.

A change is a **patch** when it fixes behaviour to match its documented intent.
That includes correcting a skill to match the command-line tool, listing a
symbol the index missed, and rewording a skill without changing its intent.

Messages on standard error, and the wording of any message, are not part of the
contract. Commands write data to standard output and everything else to standard
error.

Where a case is unclear, the expected impact on agents and users decides.

There is no preview tier until something needs one.

## Criteria

The checks that hold the standard in place are as little code as will do. An
existing tool is preferred to code uncoded writes, and configuration to a
script.

Each criterion has a measure, a bar and a check, as in dreamcatcher's standard.
Unlike dreamcatcher's, it has no code such as S1. A short title names it
everywhere, and its first line in the standard is the full statement. Where a
criterion transfers unchanged, this section says so and notes only what uncoded
measures.

### Simplicity

- **Cohesive modules.** Modules are cohesive. Transfers. The largest modules are
  `stubs.py` (471 lines) and `cli.py` (377).
- **Focused functions.** Functions do one thing. Transfers.
- **No unused exports.** Exports are used. Transfers. uncoded promises no Python
  API, so the permitted public names are those another module imports, the
  console entry point `main`, and `__version__`. Nothing is public because a
  test wanted it.
- **One way.** Each thing is done one way. Transfers. #234 is an example: two
  walks up the directory tree in `config.py`.
- **No suppressions.** Nothing is suppressed. Transfers, with zero `noqa` and
  zero `type: ignore`. The subprocess waivers in `refs.py` and
  `tests/test_refs.py` move to `[tool.ruff.lint.per-file-ignores]` with a
  comment giving the reason, as dreamcatcher does.

### Clarity

- **One vocabulary.** Transfers. The check is the `uncoded-consistency-review`
  skill, which uncoded itself ships.
- **True documents.** The enduring documents are true. uncoded's enduring
  documents are the ontology, the user stories, the architecture and this
  standard.
- **Docs by purpose.** Documentation is organised by purpose. Transfers. The
  current site already separates a tutorial (`getting-started.md`), task guides,
  references and explanation.
- **Versioned contract.** The contract is versioned. The measure is whether a
  compatibility statement gives the rules in
  [Breaking changes](#breaking-changes), and whether every breaking change has a
  changelog entry saying what the user must do. The changelog uses Breaking,
  Added, Changed and Fixed headings.
- **Accurate references.** The references agree with the tool. New, after llm.
  The measure is commands, flags, exit statuses and settings that the command
  reference, the configuration reference or a skill describes differently from
  the code. The bar is zero. The check follows llm. Under each command's
  heading, `docs/commands.md` keeps its prose and examples and gains a block
  that cog generates from that command's `--help`. The settings table in
  `docs/configuration.md` is generated from the keys `config.py` reads.
  `cog --check` runs in pre-commit, on one Python version with a fixed
  `COLUMNS`, since argparse lays out help by both. Exit statuses are held by the
  tests of each story, and the skills and the surrounding prose by review.

### Consistency

- **Machine-checked rules.** A structural rule that review keeps missing is
  checked by a machine. Transfers. uncoded's structural rules are:
  - only `refs.py` imports `subprocess` (ruff, with the per-file waiver);
  - only `sync.py` writes or removes files or directories. The empty-directory
    pruning in `skill.py` and `stubs.py` moves there, so the rule has no
    exception;
  - imports point down three layers, as they do today, and
    `docs/architecture.md` states them. `cli` is on top. The middle layer holds
    one module per artefact or tool, `namespace_map`, `stubs`, `docs_map`,
    `skill`, `body` and `refs`, and none of them imports another. The foundation
    is everything else. A test reads the import graph;
  - every generated file carries `GENERATED_MARKER` (`tests/test_markers.py`);
  - every text read and write names its encoding (PLW1514 and the runtime gate);
    and
  - every parameter is keyword-only, unless something outside uncoded passes it
    by position, when it is positional-only. Dreamcatcher's
    `require_keyword_parameters.py` checks it in pre-commit. This settles #219.
- **Fast readable tests.** The suite is fast and speaks the user's language.
  Transfers, with the bar at 60 seconds. The suite takes about 3 seconds today.
- **Current tracker.** The tracker is current. Transfers. #226 and #162 are
  candidates to close.
- **Reviewed changes.** Every change is reviewed against this standard.
  Transfers, including the exemption for Dependabot pull requests.
- **Loud failures.** The suite fails loudly. New, after nox. pytest 9's single
  `strict = true` turns on strict config, markers, xfail and parametrisation
  IDs, and the dev floor rises to `pytest>=9.0`. Each test has a timeout, scaled
  for macOS and Windows as pipx does. `-ra` is not added, as it adds output to
  every run. The check is `pyproject.toml`.

### Elegance

- **Rules not cases.** Rules, not cases. Transfers, with a ledger at
  `docs/special-cases.md`.
- **Invariants by construction.** Invariants are held by construction.
  Transfers.
- **Few concepts.** Concept economy. Transfers, against the new ontology.
- **Symmetry.** Transfers. The parallel pairs are `body` and `refs`, code and
  documentation artefacts, and the code and documentation skills. #205 is an
  example.

## Infrastructure

The standard covers code and documentation only, as dreamcatcher's does
(alimanfoo/dreamcatcher#785). `docs/standard.md` says so in one sentence.
Infrastructure is roadmap work, and each piece is kept in force by its own
check, explained where that check is configured. The exemplar named beside an
item is the one it follows.

| Work                                                                                                                                                                                                                                                              | Kept in force by                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Actions pinned to commits, read-only top-level `permissions` with job-level grants, `persist-credentials: false`, `uv sync --locked` (urllib3)                                                                                                                    | zizmor and actionlint in pre-commit                       |
| Pre-commit revisions pinned to commits                                                                                                                                                                                                                            | Dependabot updates them in that form                      |
| The rest of dreamcatcher's hooks: fix-byte-order-marker, check-illegal-windows-names, check-merge-conflict, detect-private-key, the pygrep checks against blanket `noqa` and `type: ignore`, forbid-invisible-characters and remark-validate-links (dreamcatcher) | Pre-commit                                                |
| Grouped Dependabot updates for uv, pre-commit and GitHub Actions, each with a cooldown, and dependency review on pull requests (urllib3)                                                                                                                          | `.github/dependabot.yml`, zizmor, and the review workflow |
| Linux, macOS and Windows across Python versions, with 100% branch coverage combined across platforms (nox)                                                                                                                                                        | The gate job requires every CI job                        |
| An sdist that holds `src` alone, and a wheel built from it that runs `uncoded --version` on each operating system (pipx, dreamcatcher)                                                                                                                            | A required CI job                                         |
| Trusted Publishing through a protected environment, attestations, and a check that the tag matches the built version (urllib3)                                                                                                                                    | The publish workflow, and zizmor                          |
| No `License ::` classifier beside the SPDX `license`, and no restated `src = ["src"]` for ruff                                                                                                                                                                    | validate-pyproject in pre-commit                          |
| CodeQL default setup for Python and Actions, with secret scanning and push protection                                                                                                                                                                             | Repository settings, read by the release checklist        |
| Branch protection on `main`: a pull request, the gate job and dependency review required, enforced for admins                                                                                                                                                     | Repository settings, read by the release checklist        |
| `SECURITY.md` pointing to private vulnerability reporting                                                                                                                                                                                                         | Repository settings, read by the release checklist        |

uncoded is shared, not supported, as dreamcatcher is. So:

- only collaborators can open issues and pull requests;
- Discussions are on, and the README invites ideas, suggestions and questions
  there, in dreamcatcher's words;
- `[project.urls]` gives the documentation site as Homepage, with Repository,
  Changelog and Discussions, and no Issues;
- `.github/SECURITY.md` points to the private reporting form, asks that nothing
  be reported in a discussion, and says the project promises no reply or fix
  within any time; and
- there is no code of conduct, no issue template and no contributing guide.
  `docs/contributing.md` goes. What only it says, editing the docs and changing
  indexed content, moves to `AGENTS.md`, which already holds the rest. The
  documentation's "Contribute" section becomes "Development", as in
  dreamcatcher.

CI ends in one gate job, after pipx. It runs `if: always()`, needs every other
job, and fails unless each succeeded, since GitHub counts a skipped required
check as passing. Branch protection requires that job and `dependency-review`,
which runs only on pull requests in a workflow of its own, where the gate cannot
need it. Both names are stable, so adding or renaming a job changes the
workflow, where review sees it, and not the repository settings.

Branch protection leaves "require branches to be up to date" off, because
campaigns merge stages without a merge queue, and leaves conversation resolution
off, because with one maintainer it protects nothing.

The classifier `Development Status :: 3 - Alpha` becomes `4 - Beta`, as in
dreamcatcher. A project that is shared, not supported, does not claim to be
production-ready, and the compatibility statement carries the versioning
promise.

Dependabot moves the dev dependency on ty but not `TY_VERSION` in `refs.py`, and
the two may differ. The dev ty type-checks uncoded. `TY_VERSION` decides what
`refs` reports, so raising it is a deliberate change to `refs`, released as a
patch once the integration tests pass.

Per-version Python classifiers are not added. The CI matrix is the one list of
supported versions, and `requires-python` is what installers enforce.

The release checklist covers what has no check of its own:

- adding each new Python release to the CI matrix; and
- confirming the repository settings above, which live outside the repository.

### Not adopted

- **Scorecard.** zizmor, Dependabot, CodeQL and branch protection cover the
  checks of it that matter here. The rest, such as a second approver, fuzzing
  and a badge, do not fit a one-maintainer project.
- **Mutation and property-based testing.** These are techniques, not criteria,
  and nothing so far traces to a test that ran a change without catching it.
  `hypothesis` leaves the dev dependencies until a test uses it.
- **A spell checker.** One vocabulary concerns the choice of words, which the
  consistency review checks, not their spelling.

## Ontology

The ontology lives at `docs/ontology.md`, in dreamcatcher's form: an opening
that says it is authoritative over the dated specifications, a **Definitions**
section with one heading per concept, and a **Relationships and rules** section.
It defines uncoded's terms, starting with name path, source root, doc root,
project root, index, namespace map, stub, docs map, artefact, skill and
provenance marker. Where the code, documents or issues use another word for one
of these, the ontology's word wins. Each definition names the words it replaces,
so that renames and the current-tracker triage have a list to work from.

## Stories

The user stories live at `docs/stories.md`, in dreamcatcher's form. They tell
what happens from the user's seat, in the ontology's words, citing no mechanism.
Happy paths come first, then **user errors**, things the user did, and then
**expected faults**, things outside uncoded going wrong. A bug is behaviour that
contradicts a story.

uncoded has two users, and the stories cover both:

- the **developer**, who configures uncoded, runs `sync` and `check`, and
  commits the skills; and
- the **agent**, which reads the namespace map, stubs and docs map, and runs
  `body` and `refs`.

The stories settle how uncoded handles errors, such as a file it cannot parse
(#179), a configuration it cannot accept, `uvx` missing from `PATH`, and an
index that has gone stale.

## Testing page

`docs/testing.md`, in dreamcatcher's form, says what each kind of test
establishes and what it does not, and what CI runs, including the integration
tests that spawn ty. It lives under "Development" and settles #231.

## Definition of done

Dreamcatcher's seven questions, with an eighth: any change to the agent-facing
contract has a changelog entry under **Unreleased**, under the heading that fits
it by [Breaking changes](#breaking-changes). An entry does not state a release
type. The headings imply it: any **Breaking** entry makes the next release
major, any **Added** or **Changed** entry minor, and **Fixed** alone a patch.
