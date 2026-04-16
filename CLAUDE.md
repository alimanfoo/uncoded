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

**Step 1 — Orient. Do this now, before anything else.** Your first action
in this session — before answering the user, before any other tool call —
is to read the namespace map in full:

```
Read .uncoded/namespace.yaml
```

Do this once, immediately, at session start — not "eventually" or "when
a code question comes up." Without the map loaded, design and navigation
answers will come from pretrained guesses rather than the code actually
here. The map lists every public symbol in the codebase — directories,
files, classes, methods, functions — in source order.

**Step 2 — Understand.** Before reading any `.py` source file in this repo,
read its `.pyi` stub first. Stub paths mirror source paths under
`.uncoded/stubs/`:

```
src/foo/bar.py      →  .uncoded/stubs/src/foo/bar.pyi
tests/test_foo.py   →  .uncoded/stubs/tests/test_foo.pyi
```

This applies to every file you intend to touch or reference — including
tests. The stub is sufficient for most navigation: it contains imports,
every signature with types, first-sentence docstrings, and a `L<start>`
or `L<start>-<end>` line range on every definition — public and private.
Skipping to source means reading many lines to learn what the stub would
have told you in one. If no stub exists at the expected path, the file
has no public symbols indexed — in that narrow case, read source directly.

**Step 3 — Read source, never without offset and limit.** When you need
source beyond what the stub shows, use the stub's line range:

```
Read src/foo/bar.py  offset=<start>  limit=<end - start + 1>
```

Calling Read on a `.py` file without `offset` and `limit` is a protocol
violation — it means either Step 2 was skipped, or you are reading more
of the file than the stub said you needed. The one exception is the
first Read of a stub-less file (see Step 2), which is genuinely
exploratory.
<!-- uncoded:end -->
