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
- `uncoded` runs as a pre-commit hook to keep the index in sync, and in
  CI via `pre-commit run --all-files`. Like `ruff format`: run it, and if
  it modifies files the commit or CI step fails.
- `uncoded` also maintains a navigation section in CLAUDE.md so agents
  working on any repo using uncoded get the protocol automatically.
- Source roots are configured once in `pyproject.toml` under
  `[tool.uncoded] source-roots`; no arguments needed at invocation.

## Commands

```
# Generate (or update) the namespace map, stub files, and CLAUDE.md section
uncoded

# Run tests
pytest
```

<!-- uncoded:start -->
## uncoded navigation index

This repo uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain
a navigation index for AI agents. Do not grep. Do not read whole source files.

**Step 1 — Orient.** At the start of every task, read the namespace map in full:

```
Read .uncoded/namespace.yaml
```

This lists every public symbol in the codebase — directories, files, classes,
methods, functions — in source order.

**Step 2 — Understand.** For each relevant file, read its stub. The stub path
mirrors the source path under `.uncoded/stubs/` with a `.pyi` extension:

```
src/foo/bar.py      →  .uncoded/stubs/src/foo/bar.pyi
tests/test_foo.py   →  .uncoded/stubs/tests/test_foo.pyi
```

The stub gives you imports, all signatures with types, first-sentence
docstrings, and a `L<start>` or `L<start>-<end>` line range on every
definition — including private helpers.

**Step 3 — Read.** Use line ranges from the stub to read only what you need:

```
Read src/foo/bar.py  offset=<start>  limit=<end - start + 1>
```
<!-- uncoded:end -->
