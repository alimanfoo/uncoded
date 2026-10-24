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
  scaled by platform.
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

Each criterion has a measure, a bar and a check, as in dreamcatcher's standard.
Where a criterion transfers unchanged, this section says so and notes only what
uncoded measures.

### Simplicity

- **S1. Modules are cohesive.** Transfers. The largest modules are `stubs.py`
  (471 lines) and `cli.py` (377).
- **S2. Functions do one thing.** Transfers.
- **S3. Exports are used.** Transfers. uncoded promises no Python API, so the
  permitted public names are those another module imports, the console entry
  point `main`, and `__version__`. Nothing is public because a test wanted it.
- **S4. Each thing is done one way.** Transfers. #234 is an example: two walks
  up the directory tree in `config.py`.
- **S5. Nothing is suppressed.** Transfers, with zero `noqa` and zero
  `type: ignore`. The subprocess waivers in `refs.py` and `tests/test_refs.py`
  move to `[tool.ruff.lint.per-file-ignores]` with a comment giving the reason,
  as dreamcatcher does.

### Clarity

- **C1. One vocabulary.** Transfers. The check is the
  `uncoded-consistency-review` skill, which uncoded itself ships.
- **C2. The enduring documents are true.** uncoded's enduring documents are the
  ontology, the user stories, the architecture and this standard.
- **C3. Documentation is organised by purpose.** Transfers. The current site
  already separates a tutorial (`getting-started.md`), task guides, references
  and explanation.
- **C4. The contract is versioned.** The measure is whether a compatibility
  statement gives the rules in [Breaking changes](#breaking-changes), and
  whether every breaking change has a changelog entry saying what the user must
  do. The changelog uses Breaking, Added, Changed and Fixed headings.
- **C5. The references agree with the tool.** New, after llm. The measure is
  commands, flags, exit statuses and settings that the command reference, the
  configuration reference or a skill describes differently from the code. The
  bar is zero. The check is a test that compares the command reference with the
  parser, as llm's CI does, and review for the skills.

### Consistency

- **K1. A structural rule that review keeps missing is checked by a machine.**
  Transfers. uncoded's structural rules are:
  - only `refs.py` imports `subprocess` (ruff, with the per-file waiver);
  - only `sync.py` writes or removes files or directories. The empty-directory
    pruning in `skill.py` and `stubs.py` moves there, so the rule has no
    exception;
  - only `cli.py` imports the command modules, and no module imports `cli`;
  - every generated file carries `GENERATED_MARKER` (`tests/test_markers.py`);
  - every text read and write names its encoding (PLW1514 and the runtime gate).
- **K2. The suite is fast and speaks the user's language.** Transfers, with the
  bar at 60 seconds. The suite takes about 3 seconds today.
- **K3. The tracker is current.** Transfers. #226 and #162 are candidates to
  close.
- **K4. Every change is reviewed against this standard.** Transfers, including
  the exemption for Dependabot pull requests.
- **K5. The suite fails loudly.** New, after nox. pytest runs with
  `--strict-markers`, `--strict-config` and `xfail_strict`, and each test has a
  timeout, scaled for macOS and Windows as pipx does. The check is
  `pyproject.toml`.

### Elegance

- **E1. Rules, not cases.** Transfers, with a ledger at `docs/special-cases.md`.
- **E2. Invariants held by construction.** Transfers.
- **E3. Concept economy.** Transfers, against the new ontology.
- **E4. Symmetry.** Transfers. The parallel pairs are `body` and `refs`, code
  and documentation artefacts, and the code and documentation skills. #205 is an
  example.

## Infrastructure

The standard covers code and documentation only, as dreamcatcher's does.
Infrastructure is roadmap work, and each piece is kept in force by its own check
rather than by a criterion. The exemplar named beside each item is the one it
follows.

| Work                                                                                                                                | Kept in force by                                 |
| ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Actions pinned to commits, read-only top-level `permissions`, `uv sync --locked` (urllib3)                                          | zizmor and actionlint in pre-commit              |
| Pre-commit revisions pinned to commits                                                                                              | Dependabot updates them in that form             |
| Grouped Dependabot updates for uv, pre-commit and GitHub Actions, with a cooldown, and dependency review on pull requests (urllib3) | `.github/dependabot.yml` and the review workflow |
| Linux, macOS and Windows across Python versions, with 100% branch coverage combined across platforms (nox)                          | Every CI job is a required check                 |
| The installed package runs `uncoded --version` on each operating system (pipx, dreamcatcher)                                        | A required CI job                                |
| Trusted Publishing through a protected environment, attestations, and a check that the tag matches the built version (urllib3)      | The publish workflow, and zizmor                 |
| Correct classifiers and URLs, and deliberate sdist contents                                                                         | validate-pyproject in pre-commit                 |
| Branch protection on `main`, `SECURITY.md` and private vulnerability reporting (urllib3)                                            | The release checklist                            |

Two things have no check of their own, so the release checklist covers them:

- adding each new Python release to the CI matrix; and
- confirming that branch protection and private vulnerability reporting are
  still on, since those settings live outside the repository.

### Not adopted

- **CodeQL and Scorecard.** zizmor and ruff's security rules cover the same
  ground for a project this size. Revisit if a finding slips past them.
- **Mutation and property-based testing.** These are techniques, not criteria. A
  testing page can record what each establishes if one is adopted. `hypothesis`
  leaves the dev dependencies until a test uses it.

## Ontology

The ontology lives at `docs/ontology.md`, in dreamcatcher's form: an opening
that says it is authoritative over the dated specifications, a **Definitions**
section with one heading per concept, and a **Relationships and rules** section.
It defines uncoded's terms, starting with name path, source root, doc root,
project root, index, namespace map, stub, docs map, artefact, skill and
provenance marker. Where the code, documents or issues use another word for one
of these, the ontology's word wins.

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

## Definition of done

Dreamcatcher's seven questions, with an eighth: any change to the agent-facing
contract is classed as breaking, minor or patch under
[Breaking changes](#breaking-changes), and has a changelog entry.
