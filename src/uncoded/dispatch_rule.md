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
