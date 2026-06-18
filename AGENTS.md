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

Index artefacts — generated from the configured roots:

1. **Namespace map** (`.uncoded/namespace.yaml`) — a hierarchical YAML file
   listing all symbols: directories, files, classes (with attributes
   and methods), and functions. Covers both source and tests. Loaded into
   context before any task begins. Gives the agent a world view.

2. **Stub files** (`.uncoded/stubs/`) — one `.pyi` per source file, with
   imports, full signatures (parameter names, types, return types),
   module constants, and class attributes.

3. **Doc map** (`.uncoded/docs.yaml`) — a heading outline of every Markdown
   file in configured `doc-roots`. Each file nests its ATX headings as keys.
   Agents load this to orient to the documentation, then navigate to a
   heading with `Read` or `grep`. Generated only when `doc-roots` is set.
   Outline only — no `uncoded body`, `uncoded refs`, or stubs for Markdown.

Alongside the index, uncoded ships `uncoded body` to read symbol bodies and
`uncoded refs` to find all references. See "How to read and edit code in
this codebase" below for the dispatch rule.

## Commands

This project uses [uv](https://docs.astral.sh/uv/). Run `uncoded` commands
via `uvx` so they run the published package without needing to install it;
run project tooling (`pytest`, `pre-commit`) via `uv run`.

```sh
# Generate (or update) the namespace map, stub files, docs.yaml,
# and instruction-file sections
uvx uncoded sync

# Verify the index without writing; exits non-zero if any file would change
uvx uncoded check

# Print the source body of a named symbol to stdout
uvx uncoded body <name_path> --in <relative_path>

# Find references to a symbol
uvx uncoded refs <name_path> --in <relative_path>

# Run tests (branch coverage enforced; see [tool.coverage.report]
# in pyproject.toml)
uv run pytest

# Run a subset of tests without the coverage gate
uv run pytest tests/test_stubs.py --no-cov
```

<!-- uncoded:start -->
## How to read and edit code in this codebase

This repo uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain
a symbol index over its source code, with two associated tools:
`uncoded body` for reading a symbol's body and `uncoded refs` for finding
references.
The point of this scaffolding is one rule.

### The dispatch rule

**If your search term is the name of a Python symbol — a class, function,
method, attribute, or module-level constant — use the index. If it's a
pattern, regex, or free-text phrase, use grep.**

This applies to every tool call where you are trying to find code, not
just the first one in the session. The pretrained reflex for "find X" is
grep, and that reflex is wrong here. `grep -rn 'def resolve_body'` to read a
function's body is the rule firing — that is `uncoded body`. `grep -rn
'function_name'` to check whether something has callers before a refactor is
the rule firing — that is `uncoded refs`. `grep` then `Edit` to delete
dead code is the rule firing — that is `uncoded refs` to confirm dead,
then `Edit`. The grep version of any of these is noisier and less reliable:
grep matches comments, strings, and unrelated attributes; grep misses
re-exports (so caller and delete checks come back incomplete); grep forces
offset arithmetic to slice a body. The indexed tools don't.

### How to execute the rule

The index has two parts (a namespace map and per-file stubs) and three
steps (orient, understand, act).

**Step 1 — Orient. Read the namespace map first.** Before answering the
user, before any other tool call:

```text
Read .uncoded/namespace.yaml
```

This lists every symbol in the codebase — directories, files, classes,
methods, functions. Without it loaded, "find X" answers come from
pretrained guesses about what a project like this *probably* contains,
rather than what is actually here. Read it once, in full, at session
start.

**Step 2 — Understand. Read the `.pyi` stub before any `.py` source.**
Stub paths mirror source paths under `.uncoded/stubs/`:

```text
src/foo/bar.py      →  .uncoded/stubs/src/foo/bar.pyi
tests/test_foo.py   →  .uncoded/stubs/tests/test_foo.pyi
```

Every file you intend to touch or reference, including tests. The stub
contains imports, every signature with types, module-level assignments,
and class attributes — enough for most navigation. Skipping straight to
source means reading many lines to learn what the stub would have told
you in one. If no stub exists at the expected path, the file has no
symbols indexed; in that narrow case, read source directly.

**Step 3 — Act. Use `uncoded body` to read a symbol's body;
use `uncoded refs` to find every reference to a symbol; use `Edit` (with
`uncoded body`'s output as `old_string`) to change a symbol.**
With the map and stub loaded, you have the exact `relative_path` and
`name_path` each tool needs (`ClassName/method` for a method,
`function_name` for a top-level function). Per task:

- **Read a symbol's body.** `uvx uncoded body <name_path> --in <relative_path>` —
  prints the symbol's source text to stdout, byte-identical to disk.
  Returns exactly the symbol; no offset arithmetic, no risk of reading
  too much. Its output has every byte `Edit` needs as `old_string` — no
  extra `Read` required for partial edits. Stay on stubs for a
  wider sweep.

- **Find every reference to a symbol.**
  `uvx uncoded refs <name_path> --in <relative_path>`. Prints one reference
  per line as `file:line:col`, sorted. Grep on the name misses re-exports
  and adds false positives from comments, strings, and attribute lookups
  on other types. If the next move depends on the answer being complete,
  grep cannot give you that.

- **Edit a symbol.** `uvx uncoded body <name_path> --in <relative_path>` gives
  the exact `old_string`; then `Edit` to apply the change.

- **Rename.** `uvx uncoded refs <name_path> --in <relative_path>` enumerates
  every site; then `Edit` at each.

- **Safely delete.** `uvx uncoded refs <name_path> --in <relative_path>` must
  return empty; then `Edit` to remove.

### Where Read, Edit, and grep are still the right tools

The rule is about source navigation by symbol name. Outside that, Read,
Edit, and grep stay correct:

- Free-text or pattern search outside source: Markdown, YAML, TOML,
  configs, commit messages, notebook JSON, fixture data.
- Pattern search across signatures (regex over type annotations,
  decorator usage, alias declarations) — these are not symbol-name
  lookups even though they sit inside source.
- Partial-line edits inside a symbol body, once you have retrieved it
  via `uncoded body`.
- The rare stub-less Python file that needs exploratory reading.

The dispatch rule turns on the search term: a symbol name → the index; a
regex or free-text phrase → grep.
<!-- uncoded:end -->
