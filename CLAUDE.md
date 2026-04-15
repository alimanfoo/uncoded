# uncoded

## Problem

AI coding agents navigate codebases poorly. They grep for guessed keywords,
skim the first few lines of files, and fill gaps from pretraining rather than
reading the actual code. System prompts encourage this with "make reasonable
assumptions." The result is plausible-looking output built on a hallucinated
understanding of code that's sitting right there, unread.

## Approach

Provide a static, pre-computed index that gives agents a top-down view of a
codebase. The agent loads the index at the start of a task, sees the full
vocabulary of the code, and navigates deterministically to what it needs —
no guessing, no grep.

Two-level index (phase 2 in progress):

1. **Namespace map** (.uncoded/namespace.yaml) — a hierarchical YAML file
   listing all public symbols: directories, files, classes (with attributes
   and methods), and functions. Loaded into context before any task begins.
   Gives the agent a world view and the vocabulary of the codebase.

2. **Stub files** (.pyi) — one per source file, providing full signatures
   with parameter names, types, return types, first-sentence docstrings,
   and line-range comments pointing to the implementation. The agent reads
   these to understand a file's API surface before jumping to specific line
   ranges in the source.

## Design notes

- Paths in the namespace map are repo-relative, so an agent can open any
  file directly from the key name without inferring a source root.
- The map uses a pure key hierarchy — no lists, no mixed notation. Every
  level (directory, file, symbol, member) is a YAML key. Indent to zoom in.
- Public means no leading underscore. `__init__.py` is included when it
  contains public symbols, so package-level API is not invisible.
- Source order is preserved, not alphabetized.
- The tool is designed to run as a pre-commit hook to keep the index in sync,
  and as a CI check to catch drift.

## Commands

```
# Generate (or update) the namespace map and stub files
uncoded sync src tests

# Check that the index is up to date (used in CI)
uncoded check src tests

# Run tests
pytest
```
