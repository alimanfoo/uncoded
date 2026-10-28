# uncoded

CLAUDE.md is a symlink to this file. Edit AGENTS.md.

## Problem

AI coding agents navigate codebases poorly. They grep for guessed keywords, skim
the first few lines of files, and fill gaps from pretraining rather than reading
the actual code. System prompts encourage this with "make reasonable
assumptions." The result is plausible-looking output built on a hallucinated
understanding of the code.

## Approach

A static, pre-computed index gives agents a top-down view of a codebase. The
agent loads the index at the start of a task. It sees the full vocabulary of the
code and navigates directly to what it needs, without guessing or grepping.

The index files, generated from the roots:

1. **Namespace map** (`.uncoded/namespace.yaml`). A hierarchical YAML file
   listing all symbols, beneath the directories and files that hold them:
   classes (with their methods, properties and assignments), functions and
   assignments. It covers both source and tests. The agent loads it into context
   before any task begins. The map gives the agent a world view.

2. **Stub files** (`.uncoded/stubs/`). One `.pyi` for each Python file that has
   symbols. It includes imports, signatures (parameter names, types, return
   types), and the assignments in module and class bodies.

3. **Docs map** (`.uncoded/docs.yaml`). The headings of every Markdown file
   under the doc roots. Each file nests its `#`-prefixed headings as keys.
   Agents load this to orient to the documentation, then navigate to a heading
   with `Read` or `grep`. uncoded generates it only when `doc-roots` names a
   root. Headings only. No `uncoded body`, `uncoded refs`, or stubs for
   Markdown.

Alongside the index, uncoded ships `uncoded body` to read a symbol's definition
and `uncoded refs` to find all references.

## How we decide

Test every proposed change against these questions before making it. A change
that fails one needs a strong reason.

1. **Purpose.** How does it serve uncoded's goal, to raise the recall and
   precision of agents' code reading? Judge a change against the whole project,
   not only the issue or bug report at hand.
2. **Value.** What does it gain a user, and is the gain real? A problem nobody
   has met is not yet a reason.
3. **Less, not more.** Could the same goal be reached by removing code rather
   than adding it?
4. **Evidence.** Has the code been read, and the behaviour tried, rather than
   reasoned about from memory?
5. **Cost.** Is it simple to build? Does it need new machinery, a new concept,
   or a second home for a fact? Anything new has to earn its place.
6. **Precedent.** What do the best open-source tools do? Where they disagree,
   does the reason behind the convention apply to uncoded?
7. **Common sense.** Does the rule fit the case, or would following it to the
   letter cost more than it gains?

## Commands

This project uses [uv](https://docs.astral.sh/uv/). Run the commands below via
`uv run`. `uv run uncoded` runs the code in the checkout. The pre-commit hook
runs the release that its `entry` names, and writes back any installed skill
file that a run of the checkout changed.

```sh
# Run tests. PYTHONWARNDEFAULTENCODING=1 arms the EncodingWarning gate.
# pytest enforces branch coverage. See [tool.coverage.report] in pyproject.toml.
PYTHONWARNDEFAULTENCODING=1 uv run pytest

# Run a subset of tests without the coverage gate
PYTHONWARNDEFAULTENCODING=1 uv run pytest tests/test_stubs.py --no-cov

# Run every test, the integration tests that spawn ty included
PYTHONWARNDEFAULTENCODING=1 uv run pytest -m "integration or not integration"

# Preview the documentation site at http://127.0.0.1:8000/
uv run mkdocs serve

# Build the documentation with the strict checks that mkdocs.yml sets
uv run mkdocs build

# Run the full pre-commit suite (the same checks CI runs)
uv run pre-commit run --all-files
```

## Dev setup

Clone and install dev dependencies:

```sh
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync
uv run pre-commit install
```

### Windows

`CLAUDE.md` is a symlink to `AGENTS.md`. On macOS and Linux this is transparent.
On Windows, enable git's `core.symlinks` setting. Without it, git checks out
`CLAUDE.md` as a plain text file containing the string `AGENTS.md` rather than
following the symlink.

## Linting and formatting

Run `uv run ruff check --fix` and `uv run ruff format` before committing. Both
are pinned via the `dev` optional dependency. The pre-commit hooks run the same
commands automatically. If a hook rewrites files, the commit fails. Re-stage the
modified files and commit again. The uncoded sync hook follows the same pattern
for tracked generated skill files, and the cog hook for the `--help` blocks in
`docs/commands.md`.

Never commit with `--no-verify`. CI runs `pre-commit run --all-files` on every
pull request and will fail a build where a hook was skipped.

Do not pass `--unsafe-fixes` unless a specific violation needs it. Review every
change that it makes.

A complexity-check violation means a function is too complex to pass. Refactor
or flatten it. Never suppress a complexity violation with an ignore comment and
never raise the threshold. The enabled checks and their thresholds are in
`pyproject.toml`.

The ty pre-commit hook runs the type checker. It is pinned via the `dev`
optional dependency, the same way ruff is.

## Docstrings

Public symbols need a pep257 plain-prose docstring. Magic methods are included.
Private symbols (underscore-prefixed) and test code are exempt.

## Testing

[docs/testing.md](docs/testing.md) says what each kind of test establishes, when
to run the integration tests, and what CI runs.

The test suite enforces 100% branch coverage. The threshold is set in
`[tool.coverage.report]` in `pyproject.toml`. In CI, the coverage job in
`.github/workflows/ci.yml` applies it to the coverage of every test job
combined.

Cover both arms of every branch. If an arm looks unreachable, the branch is dead
code. Remove or restructure it rather than reach for a coverage pragma. The repo
carries no coverage pragmas.

## Enduring documents

These documents hold uncoded to account.

- [docs/concepts.md](docs/concepts.md) says what the words mean. Use its words
  and no others.
- [docs/stories.md](docs/stories.md) says what users do with uncoded and what
  they see, including what happens when things go wrong. Behaviour that
  contradicts a story is a bug.
- [docs/architecture.md](docs/architecture.md) says where each thing lives in
  the code.
- [docs/standard.md](docs/standard.md) says how good the work has to be and how
  we tell.

Answer [the definition of done](docs/standard.md#definition-of-done) in every
pull request description, in the form that the standard gives.

## Conventions

This section names where each cross-cutting convention lives and what keeps it
in place.

**Provenance marker.** Every generated file carries `GENERATED_MARKER`, defined
in `src/uncoded/markers.py`. The tests verify that every output kind carries it.

**Stub style.** Every stub is laid out in the standard stub style that ruff
writes for `.pyi` files. The `stub-style` hook in `.pre-commit-config.yaml`
checks the stubs of uncoded's own source.

**Explicit encoding.** Every text read/write in the repository must pass
`encoding=`. Configuration lives in `pyproject.toml` and
`.github/workflows/ci.yml`.

The static check is ruff rule PLW1514 (unspecified-encoding), enabled in the
`select` list under `[tool.ruff.lint]`. It runs at pre-commit and in the CI lint
job, covering the whole tree. PLW1514 requires `preview = true`. Disabling
preview silently drops the rule.

PLW1514 does not resolve fixture-derived Path receivers, such as
`(tmp_path / "f.py").write_text(...)`. The runtime gate covers those calls when
they execute. A write on a never-executed line is the accepted residual.

The runtime gate turns EncodingWarning into a test failure.
`filterwarnings = ["error::EncodingWarning"]` in `[tool.pytest.ini_options]`
promotes the warning to an error. The CI test job sets
`PYTHONWARNDEFAULTENCODING=1`. Without it the interpreter never emits
EncodingWarning and the filter is inert.

Run tests locally as `PYTHONWARNDEFAULTENCODING=1 uv run pytest`. The sentinel
in `tests/test_encoding_gate.py` fails loudly if either the env var is unset or
the filterwarnings escalation is removed.

**Writes in `sync.py`.** Only `src/uncoded/sync.py` writes or removes files or
directories. The `writes-only-in-sync` hook in `.pre-commit-config.yaml` checks
it.

**Import layers.** Imports point down the three layers that
`docs/architecture.md` describes. The import-linter contract in `pyproject.toml`
checks them.

**Keyword parameters.** Every parameter is keyword-only, in `src` and `tests`.
Ruff's PLR0917, with `max-positional-args = 0` in `pyproject.toml`, checks it.

**Complexity ceiling.** The enabled complexity checks and their thresholds are
in `pyproject.toml`. See [Linting and formatting](#linting-and-formatting) for
the response to a violation.

**Special cases.** A conditional that names a particular situation, rather than
applies a general rule, has an entry in
[docs/special-cases.md](docs/special-cases.md), with its cause. Review checks
it.

**Index local.** `uncoded sync` writes `.uncoded/.gitignore`, which keeps the
whole index out of Git.

## Releasing

[docs/releasing.md](docs/releasing.md) is the checklist for a release, from
checking the standard to publishing to PyPI.

## Before you start

- Load the `uncoded-code-navigation` skill once per session, before searching,
  reading or editing any code.
- Load the `uncoded-doc-navigation` skill once per session, before searching,
  reading or editing any docs.
