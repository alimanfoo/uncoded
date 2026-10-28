# Engineering standard

This page says what uncoded holds itself to. It is one of the four enduring
documents, beside [the concepts page](concepts.md), which fixes the words,
[the stories](stories.md), which fix what users do and see, and
[the architecture](architecture.md), which fixes where each thing lives in the
code. This page says how good the result has to be, and how we tell.

The standard covers the code and its documentation. The repository's
infrastructure, such as its workflows, its dependency updates and its packaging,
is kept in force by its own checks, and each check is explained where it is
configured.

## The aim

uncoded aims to be as simple, clear, consistent and elegant as the finest open
source projects. Those four words have a precise meaning here.

- **Simple** means there is no more of it than the job needs. Each part is small
  enough to hold in mind, and each thing is done one way.
- **Clear** means a reader who knows the domain can find the code for a concept
  from its name, read it in one sitting, and is told nothing twice.
- **Consistent** means the same idea looks the same everywhere it appears, and
  every rule we state is one a reader can check.
- **Elegant** means special cases dissolve into general rules, so that nothing
  in the code is arbitrary and nothing could be taken away.

The criteria below turn each word into something we can measure.

## Exemplars

The standard is not invented from nothing. Each of the projects below sets the
bar for part of it. Each is credited only with what reading the project
verified, so that a criterion can be traced to a project that meets it. This
standard adapts the one that
[dreamcatcher](https://github.com/alimanfoo/dreamcatcher/blob/main/docs/standard.md)
keeps.

- **pre-commit.** A Python command that runs other programs, with no source file
  over 600 lines, full coverage enforced, and five runtime dependencies. It sets
  the bar for module cohesion and dependencies.
- **Trio.** Seven concepts that compose, a design document that states ranked
  principles and says what the project will not do, and naming rules written
  beside the ambiguity each prevents. It sets the bar for elegance, for
  vocabulary and for the enduring documents. Its design document has also gone
  stale in places, which is why each measurement reads ours against the code.
- **attrs and structlog.** A page that says why, a changelog with a written rule
  for what earns an entry, and a compatibility statement a reader can find. They
  set the bar for release practice.
- **Click and Flask.** Click's documentation is organised by what the reader is
  trying to do, and says so. Flask keeps its logic apart from its input and
  output. They set the bar for the shape of the documentation, and for keeping
  logic apart from input and output. Neither keeps its modules small.
- **SQLite.** A versioned file format, a compatibility promise phrased as
  intent, and a published account of how the project is tested. It sets the bar
  for the index formats and the contract. We borrow its forms, not its promises.
- **urllib3.** Every action is pinned to a commit, every workflow sets read-only
  `permissions`, zizmor runs in pre-commit, CodeQL covers `actions`, Scorecard
  runs, Dependabot groups its updates with a cooldown, publishing goes through a
  protected environment with `attestations: true`, and `SECURITY.md` gives a
  private reporting route. It sets the bar for the supply chain and releases.
- **nox.** CI runs Linux, macOS and Windows across Python versions with
  `fail-fast: false`, combines coverage from every platform and requires 100%,
  isolates platform branches behind a patchable `_PLATFORM`, and runs pytest
  with strict markers, strict config and `xfail_strict`. It sets the bar for
  cross-platform testing and for loud failures.
- **pipx.** CI tests the installed wheel, scales test timeouts by platform, and
  ends in a "Required checks pass" job that runs `if: always()`, needs every
  other job, and fails unless each succeeded. It is second to nox for testing.
- **llm.** CI fails when `docs/help.md` no longer matches the command's `--help`
  output. It sets the bar for accurate references.
- **uv and ruff.** uv separates public formats from internal ones and scales
  care to "expected real-world impact". Ruff counts a change as breaking when
  "the intent of the rule changes", and deprecates before it removes. They set
  the bar for what counts as a breaking change.

pre-commit and Trio are primary. Between them they cover structure, clarity and
elegance, which is where the greatest distance lies.

## Criteria

Each criterion has a short title, which names it everywhere, and opens with its
full statement. Each then has a **measure**, which says what number or fact we
read; a **bar**, which says what value passes; and a **check**, which says what
enforces it.

The check is a machine where a machine can tell cheaply and without false
alarms, and a reviewer everywhere else. Review is a check in its own right, not
a gap waiting for a tool. An existing tool is preferred to code uncoded writes,
and configuration to a script. A mechanical check is code, so it meets this
standard like any other code, and it earns its place only when a criterion has
failed in review more than once and the check would be small and exact. Adding
checks is not progress towards the standard. Meeting the criteria is.

### Simplicity

#### Cohesive modules

Modules are cohesive.

- Measure: modules under `src` for which review cannot name the one
  responsibility they own, read largest first.
- Bar: zero. A module is split where a clean boundary gives each part a
  responsibility of its own, never to meet a line count.
- Check: review, ordered by the line counts the measurement reports and focused
  on any module a change grows.

#### Focused functions

Functions do one thing.

- Measure: functions under `src` for which review cannot name the one job they
  do, read longest first.
- Bar: zero. A function is split where a clean seam gives each part a job of its
  own, never to meet a line count. A long function that reads as a sequence of
  steps stays whole.
- Check: review, ordered by the line counts the measurement reports and focused
  on any function a change grows. The complexity limits in `pyproject.toml` stop
  the worst cases before review.

#### No unused exports

Exports are used.

- Measure: top-level names under `src` without a leading underscore that no
  other module under `src` imports.
- Bar: zero, apart from `main`, the console entry point. uncoded promises no
  Python API, so a name is public only because another module imports it.
  Nothing is public because a test wanted it.
- Check: review.

#### One way

Each thing is done one way.

- Measure: places where two functions derive the same fact, or two types model
  the same concept.
- Bar: zero. A fact derived in one module is not derived again in another, and
  the same concept has one representation.
- Check: review, guided by
  [the consistency review](concepts.md#consistency-review).

#### No suppressions

Nothing is suppressed.

- Measure: `noqa`, `type: ignore` and `pragma: no cover` comments under `src`
  and `tests`.
- Bar: zero of each. A lint rule that must not apply to one file is waived in
  `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`, with a comment that
  gives the reason. A branch that looks unreachable is removed or restructured,
  not excluded from coverage.
- Check: the pre-commit hooks against blanket `noqa` and `type: ignore`, the
  coverage gate, and review.

### Clarity

#### One vocabulary

Each concept has one word, the one the concepts page gives it.

- Measure: disagreements that the consistency review reports between two claims
  about one concept, in code, output, documents, skills and the issue tracker,
  and uses of a word that the concepts page replaces.
- Bar: zero.
- Check: the consistency review, which uncoded ships as the
  `uncoded-consistency-review` skill, run before each major or minor release and
  on any pull request that names a concept.

#### True documents

The enduring documents are true.

- Measure: statements in the concepts page, the stories, the architecture and
  this standard that the code contradicts.
- Bar: zero. A pull request that moves the code past one of them corrects it in
  the same change and says so.
- Check: review, plus the import contract under
  [Machine-checked rules](#machine-checked-rules) for the layers that the
  architecture states.

#### Docs by purpose

Documentation is organised by purpose.

- Measure: whether a developer can install, configure, run and consult a command
  reference without reading how uncoded works inside.
- Bar: four kinds of page, kept apart: a tutorial that takes a project from
  nothing to an agent using the index, how-to pages for each task, a reference
  for every command and setting, and explanation of the design. The README is a
  short entrance to the documentation. Pages for users do not link to the pages
  under "Development".
- Check: review of the docs map, which `uncoded sync` writes.

#### Versioned contract

The contract is versioned.

- Measure: whether a compatibility statement gives the rules for what counts as
  a breaking, minor or patch change to the contract, and whether every breaking
  change has a changelog entry saying what the user must do.
- Bar: both hold, for the contract and the rules that
  [the compatibility page](compatibility.md) gives. The changelog uses the
  headings Breaking, Added, Changed and Fixed.
- Check: review, through the definition of done's
  [Changelog entry](#definition-of-done) question.

#### Accurate references

The references agree with the tool.

- Measure: commands, flags, exit statuses and settings that `docs/commands.md`,
  `docs/configuration.md` or a skill describes differently from the code.
- Bar: zero.
- Check: under each command's heading, `docs/commands.md` holds a block that cog
  generates from that command's `--help`, and `cog --check` runs in pre-commit
  on one Python version with a fixed `COLUMNS`, since argparse lays out help by
  both. The tests of each story hold the exit statuses. The consistency review
  at each release holds the skills, the prose around the generated blocks, and
  `docs/configuration.md`.

### Consistency

#### Machine-checked rules

A structural rule that review keeps missing is checked by a machine.

- Measure: structural rules that have failed review more than once, that a small
  and exact check could enforce, and that no machine checks.
- Bar: zero. These rules are checked:
  - Only `refs.py` imports `subprocess`. Ruff's subprocess rules check it, with
    a per-file waiver for `refs.py`.
  - Only `sync.py` writes or removes files or directories. A `pygrep` hook over
    `src`, excluding `sync.py`, checks it.
  - Imports point down three layers, which the architecture states. An
    import-linter `layers` contract in `pyproject.toml` checks it.
  - Every generated file carries the provenance marker. `tests/test_markers.py`
    checks it.
  - Every text read and write names its encoding. Ruff's PLW1514 and the runtime
    gate in the tests check it.
  - Every parameter is keyword-only. Ruff's `too-many-positional-arguments`
    (PLR0917), with `max-positional-args = 0`, checks it in `src` and `tests`.

  Review checks every other structural rule until it fails more than once.

- Check: the tools named beside each rule.

#### Fast readable tests

The suite is fast and speaks the user's language.

- Measure: the wall-clock time of the default test run, and the test names.
- Bar: under 60 seconds on a laptop, at 100% branch coverage. Every test is
  named for a behaviour a user could recognise, not for a function it calls.
- Check: pytest reports the time, and review reads the names.

#### Current tracker

The tracker is current.

- Measure: open issues that name a concept by a word the concepts page replaces,
  that ask for work already done, or that ask for what a story rules out.
- Bar: zero.
- Check: triage before each major or minor release.

#### Reviewed changes

Every change is reviewed against this standard.

- Measure: pull requests merged since the previous major or minor release that
  explain what they change and why, link any relevant issue or spec, and answer
  the definition of done.
- Bar: all of them, apart from the dependency updates that Dependabot raises.
  Nothing reaches `main` except through a pull request.
- Check: review, which reads the answers before the pull request merges, and
  branch protection, which requires a pull request.

#### Loud failures

The suite fails loudly.

- Measure: the pytest settings in `pyproject.toml`.
- Bar: pytest 9's `strict = true`, which turns on strict config, strict markers,
  strict xfail and strict parametrisation IDs, with `pytest>=9.0` in the dev
  dependencies; and a timeout on every test, scaled for macOS and Windows in CI.
- Check: `pyproject.toml`, read in review.

### Elegance

These criteria rest more on review than the others. An objection under them must
name the question that fails and show the evidence. Elegance is not a word for
"I would have done it differently".

#### Rules not cases

Rules, not cases.

- Measure: conditionals whose condition names a particular situation rather than
  applies a general rule, and the ledger in `docs/special-cases.md` that lists
  each one with its cause.
- Bar: every such conditional is on the ledger, and every entry has an external
  cause, such as a rule of Python's grammar or a Windows behaviour. Nothing on
  the ledger exists because of a choice this project made.
- Check: review, asking of each new branch whether it would go if a rule were
  stated more generally.

#### Invariants by construction

Invariants are held by construction.

- Measure: branches, raises and asserts that defend against a state the types
  could have made unrepresentable, such as a flag that says which of two
  optional fields is set.
- Bar: zero. Where two facts must agree, one type carries both.
- Check: review.

#### Few concepts

Concept economy.

- Measure: the change to the concepts page in each pull request, against the
  case its spec makes.
- Bar: a feature adds a concept only when its spec shows that the existing
  concepts cannot compose to it. Removing a concept needs no case.
- Check: review, through the definition of done's
  [Concepts' words](#definition-of-done) question. A spec arrives in a pull
  request like any other change.

#### Symmetry

Parallel concepts have parallel operations.

- Measure: the operations that exist for one of a parallel pair and not the
  other, or exist twice. The parallel pairs are `uncoded body` and
  `uncoded refs`, the code index and the documentation index, and the two
  navigation skills.
- Bar: each pair has parallel operations with parallel names, and shares code
  where its two halves do the same thing. An asymmetry stands only where the
  concepts page or the stories name the difference.
- Check: review, reading the namespace map, which `uncoded sync` writes.

## Definition of done

A pull request is done when its author can answer yes to each of these
questions.

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
8. **Changelog entry.** Any change to the contract has an entry under
   **Unreleased**, under the heading that fits it, as
   [the changelog](changelog.md) defines the headings. An entry does not state a
   release type, because the headings decide it.

A pull request answers each question under a "Definition of done" heading,
starting with the question's title in bold, not its number, and giving its
evidence. "Yes" alone is not an answer.

## Exceptions

A criterion may be waived for one place, never in general. The waiver is written
where the check will read it: a per-file ignore in `pyproject.toml`, with a
comment that gives the reason, for a lint rule, and an entry on the ledger for
[Rules not cases](#rules-not-cases). A waiver with no reason a reader can find
is a violation.

## Measurement

Every criterion is measured again before each major or minor release, and the
enduring documents are read against the code. [The measurement](measurement.md)
holds the latest results and says how each was taken, so the next measurement
can repeat it. Each shortfall is owned by an issue, and none holds a release
back. Where a check that this page names is not yet in place, the measurement
says so and names the issue that adds it.
