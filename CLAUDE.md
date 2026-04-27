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
   listing all symbols: directories, files, classes (with attributes
   and methods), and functions. Covers both source and tests. Loaded into
   context before any task begins. Gives the agent a world view.

2. **Stub files** (`.uncoded/stubs/`) — one `.pyi` per source file, with
   imports, full signatures (parameter names, types, return types),
   first-sentence docstrings, and `L<start>-<end>` line range comments.

## Commands

This project uses [uv](https://docs.astral.sh/uv/). Run commands via
`uv run` so they execute inside the project environment without needing
an activated venv.

```
# Generate (or update) the namespace map, stub files, and CLAUDE.md section
uv run uncoded sync

# Run tests
uv run pytest
```

<!-- uncoded:start -->
## How to read and edit code in this codebase

This repo uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain
a symbol index over its source code, designed for AI agents to navigate
deterministically rather than by grep-and-skim. For source navigation, use
the index — grep-and-skim produces a noisier, slower version of what the
index already lists in full. (For free-text search elsewhere —
Markdown, configs, commit messages — grep remains the right tool. The index
is about source.)

**Step 1 — Orient. Do this now, before anything else.** Your first action
in this session — before answering the user, before any other tool call —
is to read the namespace map in full:

```
Read .uncoded/namespace.yaml
```

Do this once, immediately, at session start — not "eventually" or "when
a code question comes up." Without the map loaded, design and navigation
answers will come from pretrained guesses rather than the code actually
here. The map lists every symbol in the codebase — directories, files,
classes, methods, functions — in source order.

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
or `L<start>-<end>` line range on every definition. Skipping to source
means reading many lines to learn what the stub would have told you in
one. If no stub exists at the expected path, the file has no symbols
indexed — in that narrow case, read source directly.

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

**For symbol-level operations — use Serena.** Where Serena's MCP tools
are available (`mcp__serena__*` in the tool list), prefer them over
Read / Edit / grep for anything that operates on a symbol as a unit.
The namespace map gives you the exact `name_path` and `relative_path`
these tools take as input — e.g. `ClassName/method` for a method,
`function_name` for a top-level function.

- **Read one symbol body.** `find_symbol` with `include_body=True`
  returns exactly the symbol — no `offset` / `limit` arithmetic, no
  risk of reading too much. Often easier than the Step 3 dance for a
  single function or method. (Stay on stubs for a wider sweep.)
- **Find callers, or check whether a symbol is dead.**
  `find_referencing_symbols` returns every reference resolved by the
  language server. Do not grep for the name — grep hits comments,
  strings, attribute lookups on unrelated types, and re-exports.
- **Rename.** `rename_symbol` updates every reference across the
  codebase in one call. Multi-file find-and-replace misses imports
  and re-exports and racks up false positives.
- **Edit a whole symbol.** `replace_symbol_body`,
  `insert_before_symbol`, and `insert_after_symbol` operate on the
  symbol as a unit. Immune to the Edit tool's "string not unique"
  failure mode, never accidentally modify a similarly-named
  neighbour, and keep surrounding indentation consistent.
- **Delete a symbol.** `safe_delete_symbol` checks for live
  references before removing — dead code goes cleanly, live code
  stays put.

Reach for Read + Edit when Serena does not fit: free-text files
(Markdown, YAML, configs), partial-line edits inside a function
body, or the rare stub-less Python file that needs exploratory
reading.
<!-- uncoded:end -->
