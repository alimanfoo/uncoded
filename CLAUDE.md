# uncoded

## Problem

AI coding agents navigate codebases poorly. They grep for guessed keywords,
skim the first few lines of files, and fill gaps from pretraining rather than
reading the actual code. System prompts encourage this with "make reasonable
assumptions." The result is plausible-looking output built on a hallucinated
understanding of code that's sitting right there, unread.

## Approach

A static, pre-computed index gives agents a top-down view of a codebase.
The agent loads the index at the start of a task, sees the full vocabulary
of the code, and navigates deterministically to what it needs — no guessing,
no grep.

Two-level index:

1. **Namespace map** (`.uncoded/namespace.yaml`) — a hierarchical YAML file
   listing all public symbols: directories, files, classes (with attributes
   and methods), and functions. Covers both source and tests. Loaded into
   context before any task begins. Gives the agent a world view.

2. **Stub files** (`.uncoded/stubs/`) — one `.pyi` per source file, with
   imports, full signatures (parameter names, types, return types),
   first-sentence docstrings, and `L<start>-<end>` line range comments.
   Includes all symbols — public and private — so agents can follow calls
   into implementation detail without grepping.

## Navigation protocol

1. **Load** `.uncoded/namespace.yaml` — orient, identify relevant files and
   symbols.
2. **Read** stub files for those files — understand signatures, find line
   ranges.
3. **Read** specific line ranges in the source — implementation detail only
   where needed.

No grepping. No reading whole files. No guessing.

## Design notes

- Paths in the namespace map are repo-relative, so an agent can open any
  file directly from the key without inferring a source root.
- The map uses a pure key hierarchy — no lists, no mixed notation. Every
  level (directory, file, symbol, member) is a YAML key. Indent to zoom in.
- The namespace map lists only public symbols (no leading underscore).
  Stubs include everything, since agents navigating implementation need
  private helpers too. The `_` prefix is sufficient distinction.
- `__init__.py` is included when it contains public symbols, so
  package-level API is not invisible.
- Source order is preserved, not alphabetized.
- `uncoded sync` runs as a pre-commit hook to keep the index in sync.
  `uncoded check` runs in CI to catch drift.

## Commands

```
# Generate (or update) the namespace map and stub files
uncoded sync src tests

# Check that the index is up to date (used in CI)
uncoded check src tests

# Run tests
pytest
```
