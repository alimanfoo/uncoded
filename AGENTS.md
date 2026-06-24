# uncoded

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

This project uses [uv](https://docs.astral.sh/uv/). Run `uncoded` commands via
`uvx` so they run the published package without needing to install it. Run
project tooling (`pytest`, `pre-commit`) via `uv run`. If you are contributing
to uncoded itself and need to exercise local changes, use `uv run uncoded ...`
instead. `uvx` always runs the published release.

```sh
# Install dev dependencies (required for pytest and pre-commit)
uv sync --extra dev

# Generate (or update) the namespace map, stub files, docs.yaml, and skill files
uvx uncoded sync

# Verify the index without writing. It exits non-zero if any file would change
uvx uncoded check

# Print the source body of a named symbol to stdout
uvx uncoded body <name_path> --in <relative_path>

# Find references to a symbol
uvx uncoded refs <name_path> --in <relative_path>

# Run tests. pytest enforces branch coverage. See [tool.coverage.report]
# in pyproject.toml.
uv run pytest

# Run a subset of tests without the coverage gate
uv run pytest tests/test_stubs.py --no-cov
```

## Docstrings

Public symbols need a pep257 plain-prose docstring. Magic methods are included.
Private symbols (underscore-prefixed) and test code are exempt.

## Skills

Always load the `uncoded-code-navigation` and `uncoded-doc-navigation` skills.
