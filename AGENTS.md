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
   first-sentence docstrings, module constants, and class attributes.

Alongside the index, uncoded also ships a one-shot setup for a language
server, so agents can find references, rename, and safely delete symbols
by name rather than via grep and text edits. See "How to read and edit
code in this codebase" below for the dispatch rule.

## Commands

This project uses [uv](https://docs.astral.sh/uv/). Run commands via
`uv run` so they execute inside the project environment without needing
an activated venv.

```
# Generate (or update) the namespace map, stub files, and instruction-file section
uv run uncoded sync

# Run tests
uv run pytest
```

<!-- uncoded:start -->
## How to read and edit code in this codebase

This repo uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain
a symbol index over its source code, with
[Serena](https://github.com/oraios/serena) providing language-server-backed
tools over that index. The point of this scaffolding is one rule.

### The rule

**If your search term is the name of a Python symbol — a class, function,
method, attribute, or module-level constant — use the index. If it's a
pattern, regex, or free-text phrase, use grep.**

This applies to every tool call where you are trying to find code, not
just the first one in the session. The pretrained reflex for "find X" is
grep, and that reflex is wrong here. `grep -rn 'WriteResult'` to locate a
class is the rule firing — that is `find_symbol`. `grep -rn 'function_name'`
to check whether something has callers before a refactor is the rule
firing — that is `find_referencing_symbols`. `grep` then `Edit` to delete
dead code is the rule firing — that is `safe_delete_symbol`. The grep
version of any of these is noisier and less complete: grep misses
re-exports, and adds false positives from comments, strings, and unrelated
attribute lookups on other types. The language server does not.

### How to execute the rule

The index has two parts (a namespace map and per-file stubs) and three
steps (orient, understand, act).

**Step 1 — Orient. Read the namespace map first.** Before answering the
user, before any other tool call:

```
Read .uncoded/namespace.yaml
```

This lists every symbol in the codebase — directories, files, classes,
methods, functions — in source order. Without it loaded, "find X"
answers come from pretrained guesses about what a project like this
*probably* contains, rather than what is actually here. Read it once,
in full, at session start.

**Step 2 — Understand. Read the `.pyi` stub before any `.py` source.**
Stub paths mirror source paths under `.uncoded/stubs/`:

```
src/foo/bar.py      →  .uncoded/stubs/src/foo/bar.pyi
tests/test_foo.py   →  .uncoded/stubs/tests/test_foo.pyi
```

Every file you intend to touch or reference, including tests. The stub
contains imports, every signature with types, module-level assignments,
class attributes, and first-sentence docstrings — enough for most
navigation. Skipping straight to source means reading many lines to
learn what the stub would have told you in one. If no stub exists at
the expected path, the file has no symbols indexed; in that narrow
case, read source directly.

**Step 3 — Act. Use Serena to find, read, rename, edit, and delete symbols.**
With the map and stub loaded, you have the exact `relative_path` and
`name_path` each Serena tool needs (`ClassName/method` for a method,
`function_name` for a top-level function). Per task:

- **Find a symbol's definition, or read its body.** `find_symbol` —
  with `include_body=True` when you need implementation detail the
  stub does not show. Returns exactly the symbol; no offset arithmetic,
  no risk of reading too much. Stay on stubs for a wider sweep.

- **Find callers, or check whether a symbol is dead.**
  `find_referencing_symbols`. Returns every reference resolved by the
  language server — every import, every call site, every re-export.
  Grep on the name misses re-exports and adds false positives from
  comments, strings, and attribute lookups on other types. If the
  next move depends on the answer being complete, grep cannot give
  you that.

- **Rename.** `rename_symbol`. Updates every reference across the
  codebase in one call. Multi-file find-and-replace misses imports
  and re-exports and racks up substring false positives.

- **Edit a symbol as a unit.** `replace_symbol_body`,
  `insert_before_symbol`, `insert_after_symbol`. Immune to the Edit
  tool's "string not unique" failure mode, never modify a similarly
  named neighbour, and keep surrounding indentation consistent.

- **Delete a symbol.** `safe_delete_symbol` — not Edit, and not Edit
  after a manual reference check. The tool fuses two operations: it
  finds every reference, refuses to delete if any are live, and
  removes the symbol cleanly only when it is truly dead. The two-step
  version (find references with grep or `find_referencing_symbols`,
  then Edit) can drift — the reference check goes stale the moment
  any file changes between the calls. Whenever the task is "remove
  this symbol," regardless of how dead it looks, this is the tool.

Skip `activate_project` and `check_onboarding_performed`. The project
is already active by default, and `check_onboarding_performed` only
gates Serena's `onboarding` flow — which writes memories that uncoded
deliberately disables. Both calls produce only noise.

### Where Read, Edit, and grep are still the right tools

The rule is about source navigation by symbol name. Outside that, the
non-Serena tools stay correct:

- Free-text or pattern search outside source: Markdown, YAML, TOML,
  configs, commit messages, notebook JSON, fixture data.
- Pattern search across signatures (regex over type annotations,
  decorator usage, alias declarations) — these are not symbol-name
  lookups even though they sit inside source.
- Partial-line edits inside a symbol body, once you have retrieved it
  through Serena.
- Environments where Serena is unavailable, or the rare stub-less
  Python file that needs exploratory reading.

The dispatch test is the search term: a symbol name → Serena; a regex
or free-text phrase → grep.
<!-- uncoded:end -->
