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

Index artefacts, generated from the configured roots:

1. **Namespace map** (`.uncoded/namespace.yaml`). A hierarchical YAML file
   listing all symbols: directories, files, classes (with attributes and
   methods), and functions. It covers both source and tests. The agent loads it
   into context before any task begins. The map gives the agent a world view.

2. **Stub files** (`.uncoded/stubs/`). One `.pyi` per source file. It includes
   imports, full signatures (parameter names, types, return types), module
   constants, and class attributes.

3. **Doc map** (`.uncoded/docs.yaml`). A heading outline of every Markdown file
   in configured `doc-roots`. Each file nests its `#`-prefixed headings as keys.
   Agents load this to orient to the documentation, then navigate to a heading
   with `Read` or `grep`. uncoded generates it only when `doc-roots` is set.
   Outline only. No `uncoded body`, `uncoded refs`, or stubs for Markdown.

Alongside the index, uncoded ships `uncoded body` to read symbol bodies and
`uncoded refs` to find all references. See "How to read and edit code in this
codebase" below for the dispatch rule.

## Commands

This project uses [uv](https://docs.astral.sh/uv/). Run all commands via
`uv run`. `uvx uncoded` runs the published PyPI release, not the local editable
install. It strips the provenance marker from generated files and reports every
stub as "would update".

```sh
# Generate (or update) the namespace map, stub files, docs.yaml, and skill files
uv run uncoded sync

# Verify the index without writing. It exits non-zero if any file would change
uv run uncoded check

# Print the source body of a named symbol to stdout
uv run uncoded body <name_path> --in <relative_path>

# Find references to a symbol
uv run uncoded refs <name_path> --in <relative_path>

# Run tests. pytest enforces branch coverage. See [tool.coverage.report]
# in pyproject.toml.
uv run pytest

# Run a subset of tests without the coverage gate
uv run pytest tests/test_stubs.py --no-cov

# Run the full pre-commit suite (the same checks CI runs)
uv run pre-commit run --all-files
```

## Dev setup

Clone and install dev dependencies:

```sh
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync --extra dev
uv run pre-commit install
```

Run `uv sync --extra dev` before the first pre-commit run in a clean checkout.
The ty hook type-checks `src` and `tests`. The test modules import dev-only
packages such as pytest and hypothesis. Without the dev extras in the venv, ty
cannot resolve those imports and reports spurious errors.

This repo uses uncoded on itself. The pre-commit hook runs `uv run uncoded sync`
on each commit. If the hook modifies generated files, the commit fails. Re-stage
and commit again.

### Windows

`CLAUDE.md` is a symlink to `AGENTS.md`. On macOS and Linux this is transparent.
On Windows, enable git's `core.symlinks` setting. Without it, git checks out
`CLAUDE.md` as a plain text file containing the string `AGENTS.md` rather than
following the symlink.

## Linting and formatting

Run `uv run ruff check --fix` and `uv run ruff format` before committing. Both
use ruff 0.15.19, pinned via the `dev` optional dependency. The pre-commit hooks
run the same commands automatically. If a hook rewrites files, the commit fails.
Re-stage the modified files and commit again. The uncoded sync hook follows the
same pattern.

Never commit with `--no-verify`. CI runs `pre-commit run --all-files` on every
pull request and will fail a build where a hook was skipped.

Do not pass `--unsafe-fixes` unless a specific violation needs it and you have
reviewed the change.

A C901 violation means a function is too complex to pass the check. Refactor or
flatten it rather than raising the `max-complexity` threshold.

The ty pre-commit hook runs the type checker, pinned at 0.0.53 via `TY_VERSION`
in `src/uncoded/refs.py`.

## Docstrings

Public symbols need a pep257 plain-prose docstring. Magic methods are included.
Private symbols (underscore-prefixed) and test code are exempt.

## Releasing

GitHub releases publish to PyPI through `.github/workflows/publish.yml`. The
workflow uses PyPI Trusted Publishing. It does not need a `PYPI_TOKEN` or any
other long-lived publishing secret.

The PyPI trusted publisher is configured for:

- PyPI project: `uncoded`
- Owner: `alimanfoo`
- Repository: `uncoded`
- Workflow: `publish.yml`
- Environment: `pypi`

Create and publish a GitHub release from the release tag. The `published`
release event builds the source distribution and wheel, then uploads them to
PyPI.

## Before you start

- Load the `uncoded-code-navigation` skill before searching, reading or editing
  any code.
- Load the `uncoded-doc-navigation` skill before searching, reading or editing
  any docs.
