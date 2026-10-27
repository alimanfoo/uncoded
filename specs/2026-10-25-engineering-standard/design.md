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

- removes or renames a command, a flag, a configuration key or a generated
  file's path, or changes its meaning or default;
- changes an exit status, or the format of the data a command writes to standard
  output;
- changes a generated file's layout rules, such as how keys nest or which keys
  end in `/`, as opposed to which symbols or headings it lists;
- changes the intent of a skill, by removing, reversing or narrowing an
  instruction or reordering a workflow step; or
- drops support for a Python version.

A change is a **minor** release when it adds a command, flag, configuration key,
generated file or skill guidance, or deprecates something with a warning.
Removing a deprecated feature is breaking.

A change is a **patch** when it fixes behaviour to match its documented intent.
That includes correcting a skill to match the command-line tool, listing a
symbol the index missed, and rewording a skill without changing its intent.

Messages on standard error, and the wording of any message, are not part of the
contract. Commands write data to standard output and everything else to standard
error.

Where a case is unclear, the expected impact on users decides.

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
  documents are the concepts page, the stories, the architecture and this
  standard.
- **Docs by purpose.** Documentation is organised by purpose. Transfers. The
  current site already separates a tutorial (`getting-started.md`), task guides,
  references and explanation.
- **Versioned contract.** The contract is versioned. The measure is whether a
  compatibility statement gives the rules in
  [Breaking changes](#breaking-changes), and whether every breaking change has a
  changelog entry saying what the user must do. The changelog uses Breaking,
  Added, Changed and Fixed headings, in dreamcatcher's form. Its history is
  rebuilt briefly from the GitHub releases: one entry for each release from
  1.0.0, linking it, and one line for the 0.x releases.
- **Accurate references.** The references agree with the tool. New, after llm.
  The measure is commands, flags, exit statuses and settings that
  `docs/commands.md`, `docs/configuration.md` or a skill describes differently
  from the code. The bar is zero. The check follows llm. Under each command's
  heading, `docs/commands.md` keeps its prose and examples and gains a block
  that cog generates from that command's `--help`. `cog --check` runs in
  pre-commit, on one Python version with a fixed `COLUMNS`, since argparse lays
  out help by both. Exit statuses are held by the tests of each story. The
  skills, the surrounding prose and `docs/configuration.md`, which has only two
  settings, are held by the consistency review at each release.

### Consistency

- **Machine-checked rules.** A structural rule that review keeps missing is
  checked by a machine. Transfers. uncoded's structural rules are:
  - only `refs.py` imports `subprocess` (ruff, with the per-file waiver);
  - only `sync.py` writes or removes files or directories. The empty-directory
    pruning in `skill.py` and `stubs.py` moves there, so the rule has no
    exception. A pre-commit `pygrep` hook over `src`, excluding `sync.py`,
    matches calls such as `.write_text(`, `.unlink(`, `.rmdir(` and `.mkdir(`;
  - imports point down three layers, as they do today, and
    `docs/architecture.md` states them. `cli` is on top. The middle layer holds
    one module per generated file or tool, `namespace_map`, `stubs`, `docs_map`,
    `skill`, `body` and `refs`, and none of them imports another. The foundation
    is everything else. An import-linter `layers` contract in `pyproject.toml`
    lists them, with the middle layer's modules separated by `|` so they are
    independent, and `exhaustive = true` so a new module fails until it is
    placed;
  - every generated file carries `GENERATED_MARKER` (`tests/test_markers.py`);
  - every text read and write names its encoding (PLW1514 and the runtime gate);
    and
  - every parameter is keyword-only. Ruff's `too-many-positional-arguments`
    (PLR0917) with `max-positional-args = 0` checks it, in place of
    dreamcatcher's script. It counts positional-only parameters too, so a
    parameter that something outside uncoded passes by position needs a per-file
    ignore with its reason. `src` has none today. Tests are not exempt: pytest
    passes fixtures and parameters by name, so a test takes them after `*`, as
    `def test_sync(*, tmp_path)`. This settles #219.
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
- **Few concepts.** Concept economy. Transfers, against the concepts page.
- **Symmetry.** Transfers. The parallel pairs are `uncoded body` and
  `uncoded refs`, the code and documentation indexes, and the two navigation
  skills. #205 is an example.

## Infrastructure

The standard covers code and documentation only, as dreamcatcher's does
(alimanfoo/dreamcatcher#785). `docs/standard.md` says so in one sentence.
Infrastructure is roadmap work, and each piece is kept in force by its own
check, explained where that check is configured. The exemplar named beside an
item is the one it follows.

| Work                                                                                                                                                                                                                                                                                                                                                                                 | Kept in force by                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Actions pinned to commits, read-only top-level `permissions` with job-level grants, `persist-credentials: false`, `uv sync --locked` (urllib3)                                                                                                                                                                                                                                       | zizmor and actionlint in pre-commit                                                  |
| Pre-commit revisions pinned to commits                                                                                                                                                                                                                                                                                                                                               | Dependabot updates them in that form                                                 |
| `hatchling` and `hatch-vcs` pinned exactly in `[build-system] requires`, since `uv.lock` does not cover build requirements (dreamcatcher)                                                                                                                                                                                                                                            | Dependabot updates them in that form                                                 |
| The rest of dreamcatcher's hooks: fix-byte-order-marker, check-illegal-windows-names, check-merge-conflict, detect-private-key, the pygrep checks against blanket `noqa` and `type: ignore`, a `pygrep` hook against U+00A0 and the zero-width and bidirectional characters, in place of dreamcatcher's forbid-invisible-characters script, and remark-validate-links (dreamcatcher) | Pre-commit                                                                           |
| Grouped Dependabot updates for uv, pre-commit and GitHub Actions, each with a cooldown, and dependency review on pull requests (urllib3)                                                                                                                                                                                                                                             | `.github/dependabot.yml`, zizmor, and the review workflow                            |
| Linux, macOS and Windows with Python 3.12 to 3.15, each job confirming the interpreter it asked for, with 100% branch coverage combined across platforms (nox), and pre-commit on Windows as well as Linux (dreamcatcher)                                                                                                                                                            | The gate job requires every CI job                                                   |
| An sdist that holds `src` alone, and a wheel built from it that runs `uncoded --version` on each operating system (pipx, dreamcatcher)                                                                                                                                                                                                                                               | A required CI job                                                                    |
| Trusted Publishing through the `pypi` environment, which only tags matching `v*` may deploy to, with no required reviewer; the attestations the publish action makes by default; and a check that the tag matches the built version (urllib3)                                                                                                                                        | The publish workflow, zizmor, and the environment rule read by the release checklist |
| No `License ::` classifier beside the SPDX `license`, and no restated `src = ["src"]` for ruff                                                                                                                                                                                                                                                                                       | validate-pyproject checks the metadata; dropping the ruff setting is a one-off       |
| CodeQL default setup for Python and Actions, with secret scanning and push protection                                                                                                                                                                                                                                                                                                | Repository settings, read by the release checklist                                   |
| Branch protection on `main`: a pull request, the gate job and dependency review required, enforced for admins                                                                                                                                                                                                                                                                        | Repository settings, read by the release checklist                                   |
| `SECURITY.md` pointing to private vulnerability reporting                                                                                                                                                                                                                                                                                                                            | Repository settings, read by the release checklist                                   |

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
workflow, where review sees it, and not the repository settings. Dependency
review reads the repository's dependency graph, so the graph must be turned on
in the repository settings.

Branch protection leaves "require branches to be up to date" off, because
campaigns merge stages without a merge queue, and leaves conversation resolution
off, because with one maintainer it protects nothing.

The classifier `Development Status :: 3 - Alpha` becomes `4 - Beta`, as in
dreamcatcher. A project that is shared, not supported, does not claim to be
production-ready, and the compatibility statement carries the versioning
promise.

Dependabot moves the dev dependency on ty but not `TY_VERSION` in `refs.py`, and
the two may differ. The dev ty type-checks uncoded. `TY_VERSION` decides what
`uncoded refs` reports, so raising it is a deliberate change to `uncoded refs`,
released as a patch once the integration tests pass.

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

## Concepts

The concepts page lives at `docs/concepts.md`, in dreamcatcher's form: an
opening that says it is authoritative over the dated specifications, a **Terms**
section with one entry per term, and a **Relationships and rules** section. It
was written as `docs/ontology.md` in #260 and renamed in #261, because
"concepts" is plain English and lines up with the "few concepts" criterion. It
defines uncoded's terms, settled with the product owner, and is the one place
they are listed. Where the code, documents, skills or issues use another word
for one of these, the concepts page's word wins. The documentation names its
reader, the developer or the agent, and addresses neither as "you", because both
read it. Each entry ends with the words its term replaces, so that renames and
the current-tracker triage have a list to work from.

## Stories

The stories live at `docs/stories.md`, in dreamcatcher's form, settled with the
product owner in #261. They open with why uncoded exists, to raise the recall
and precision of an agent's code reading, which is an untested hypothesis
(#288), and with how it is used. They then tell what happens from the user's
seat, in the concepts page's words, citing no mechanism. Happy paths come first,
for the developer and then the agent, then **user errors**, things the user did,
and then **expected faults**, things outside uncoded going wrong. A bug is
behaviour that contradicts a story.

uncoded has two users, and the stories cover both:

- the **developer**, who sets uncoded up with `uncoded init` and commits the
  configuration file and the installed skill files, while agents, or tools the
  developer sets up such as a pre-commit hook or CI, run `uncoded sync` and
  `uncoded check`; and
- the **agent**, which reads the namespace map, stubs and docs map, and runs
  `uncoded body`, `uncoded refs` and `uncoded sync`.

A property's definition is its getter's, so `uncoded body` keeps printing only
the getter: a setter or deleter need not follow it in the file, and what
`uncoded body` prints must be one unbroken stretch an agent can replace.
Alternatives are recorded in #291.

### Behaviour changes

The stories settle the following changes to what uncoded does today. Stage 13 of
the roadmap builds them, one pull request each, with tests and a changelog
entry, apart from paths on Windows, which stage 7 builds. Together they make a
major release.

Settled in #260:

- **Every command works inside a project** (**Breaking**). Each finds the
  project directory by walking up from the current directory to the nearest
  configuration file, as ruff, pytest and uv do. Today `uncoded body` needs no
  configuration file and `uncoded refs` walks up from the file it is given.
  Running `uncoded body` or `uncoded refs` outside a project becomes a user
  error, and so does an `--in` file outside the project directory, as a root
  outside it already is. `--in` paths stay relative to the current directory,
  and the code navigation skill tells an agent to run `uncoded body` and
  `uncoded refs` from the project directory, where the namespace map's paths
  work as given.
- **A reference includes the symbol's definition and its imports** (**Fixed**).
  `uncoded refs` lists every location ty returns with `includeDeclaration` set,
  where today it lists only uses. The code navigation skill's rename and
  safe-delete guidance changes to match: a delete is safe when the symbol is
  unused, as the concepts page defines it.
- **The search for the configuration file passes over a `pyproject.toml` without
  a `[tool.uncoded]` table** (**Fixed**), as ruff's passes over one without
  `[tool.ruff]`. Today it stops there, so a Python package's own
  `pyproject.toml` inside the project hides the configuration file above it.

Settled in #261:

- **`uncoded init`** (**Added**). It finds an existing configuration file the
  way every command does. Finding none, it writes `.uncoded.toml` in the current
  directory, with whichever of `src` and `tests` exist as source roots and
  whichever of `README.md`, `AGENTS.md` and `docs` exist as doc roots, and with
  the required version set to its own version. It never edits `pyproject.toml`.
  If none of those roots exist, it writes no configuration file, says what it
  looked for and how to write the file by hand, and exits with status `1`. An
  existing configuration file is left as it is, and `uncoded init` says so. It
  then runs `uncoded sync`, says what to commit, and prints the lines for
  `AGENTS.md` or `CLAUDE.md` that tell agents to load the navigation skills, one
  for each kind of root the project has, saying that without them agents load
  the uncoded skills only when they choose to. It edits neither file, because
  version 2 deliberately stopped uncoded writing into them. It is safe to run
  again. `docs/getting-started.md` and `docs/keeping-current.md` change to
  match, and no longer tell the developer to run `uncoded sync`.
  `docs/keeping-current.md` also stops suggesting `uncoded check` for CI: the
  index is never committed, so in a fresh checkout `uncoded check` always
  reports it as stale. A pre-commit hook that runs `uncoded sync` is the check
  that works in CI.
- **The required version** (**Added**). A `required-version` setting names one
  exact version, such as `"3.1.0"`, with no wider specifiers, so that uncoded
  needs no new dependency. Every command at any other version stops before doing
  anything, says which version the project needs, and gives the command
  `uvx uncoded@<version> <command>`. The reason is that `uvx` caches one version
  per user and shares it across projects, so without a pin one project's upgrade
  becomes every project's, and machines disagree about the installed skill
  files, so a pre-commit hook that runs `uncoded sync` in CI, with an empty
  cache and so the newest release, fails on the day of a release. The skills do
  not carry the version: agents adapt from the message. A pre-commit hook's
  command names the version, as `uvx uncoded@<version> sync`, so upgrading means
  raising the version in the configuration file and in the hook.
- **A configuration file that cannot be read gives one line** (**Fixed**). When
  the configuration file is not valid TOML, a setting has the wrong type, or
  `required-version` is not one exact version, uncoded names the file and the
  problem, exits with status `1` and writes nothing. Today these give a Python
  traceback, or a misleading message such as "source root s is not a directory"
  for `source-roots = "src"`.
- **Every root is checked before anything is written** (**Fixed**). Today a bad
  doc root is found only after the code index and all six installed skill files
  are written. The message also says whether a root is missing or the wrong
  kind, where today a missing root is reported as "not a directory".
- **Skipped files are counted** (**Fixed**). `uncoded sync` ends with a line
  saying how many files it skipped, which settles #179. The exit status stays
  `0`.
- **Agents run `uncoded sync` at the start of every session** (**Fixed**). The
  navigation skills tell the agent to run it before reading the maps, and again
  after it changes indexed files or notices that files have changed under it.
  Today they say to run it only if the map is missing.
- **ty failures are reported** (**Fixed**). `uncoded refs` passes on what ty or
  `uvx` said about why ty failed, where today it discards it. It never reports a
  failure of ty as a fault in the `--in` file. It has no time limit: one would
  need a background thread or a way of waiting on a pipe that works on Windows,
  and nobody has reported ty hanging.
- **A generated file that cannot be read, written or removed gives one line**
  (**Fixed**). When `uncoded sync` or `uncoded check` cannot read, write or
  remove a generated file, it says which file and why, in place of a Python
  traceback. Two `uncoded sync` runs at once can meet this, and uncoded adds no
  lock to prevent it: nobody has reported the race, and a lock is new machinery.
- **Paths use `/` on every system** (**Breaking**). `uncoded refs` output,
  `uncoded sync` messages and warnings, and the path comment in each stub use
  `/` on Windows too, as the namespace map and docs map already do.
- **Messages point to `uncoded init`** where a configuration file is missing.
- **Only the current skills are removed** (**Changed**). `uncoded sync` stops
  removing the skill names of earlier versions of uncoded, `coherence-review`,
  `uncoded-coherence-review` and `uncoded-review`, which today it deletes on
  every run whoever wrote them. It removes only skills the current version
  generates, when the roots they belong with are gone. A project that still has
  an old-named skill deletes it by hand, as `docs/upgrading.md` says.

The stories record every one of these changes.

## Testing page

`docs/testing.md`, in dreamcatcher's form, says what each kind of test
establishes and what it does not, and what CI runs, including the integration
tests that spawn ty. It lives under "Development" and settles #231.

## Definition of done

Dreamcatcher's seven questions, with an eighth, each named by a short title
rather than a number:

1. **Explained.** It says what it changes and why, and links any issue or spec.
2. **Checks pass.** The tests and every required check pass, and none is
   suppressed or bypassed.
3. **Small and used.** What it adds meets cohesive modules and focused
   functions, and nothing it exports lacks a caller.
4. **Concepts' words.** Every word it introduces is on the concepts page, or the
   concepts page grew in the same change.
5. **Documents still true.** Any enduring document it makes false, it corrects.
6. **Replaced things removed.** It removes what it replaces.
7. **Conditionals are rules.** Every conditional it adds applies a rule, or is
   on the ledger with its external cause.
8. **Changelog entry.** Any change to the agent-facing contract has an entry
   under **Unreleased**, under the heading that fits it by
   [Breaking changes](#breaking-changes). An entry does not state a release
   type. The headings imply it: any **Breaking** entry makes the next release
   major, any **Added** or **Changed** entry minor, and **Fixed** alone a patch.

A pull request answers each under a "Definition of done" heading, starting with
the title in bold, not the number, and giving its evidence. "Yes" alone is not
an answer.
