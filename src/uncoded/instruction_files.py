"""Maintain the uncoded navigation section in agent instruction files.

Different coding agents read different instruction files from a repo's root.
Claude Code reads ``CLAUDE.md``; an emerging cross-agent convention uses
``AGENTS.md``. Until the ecosystem converges, a project that wants to support
both populations needs both files, with the same navigation guidance in each.
Two configurations work: keep the two files as separate copies (sync writes
each), or symlink one to the other (sync dedupes by inode and writes once).
This module owns a delimited section in any such file and keeps it in sync.
"""

from pathlib import Path

from uncoded.sync import sync_file

MARKER_START = "<!-- uncoded:start -->"
MARKER_END = "<!-- uncoded:end -->"

DEFAULT_INSTRUCTION_FILES = [Path("CLAUDE.md"), Path("AGENTS.md")]

_SECTION_BODY = """\
## How to read and edit code in this codebase

This repo uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain
a symbol index over its source code, with
[Serena](https://github.com/oraios/serena) providing language-server-backed
tools over that index. The point of this scaffolding is one rule.

### The dispatch rule

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

The dispatch rule turns on the search term: a symbol name → Serena; a
regex or free-text phrase → grep."""

SECTION = f"{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n"


def generate_section() -> str:
    """Return the full delimited uncoded section for an instruction file."""
    return SECTION


def _replace_or_append(existing: str, section: str) -> str:
    """Replace the delimited section in existing text, or append it if absent."""
    start = existing.find(MARKER_START)
    end = existing.find(MARKER_END)
    if start != -1 and end != -1 and start < end:
        before = existing[:start]
        after = existing[end + len(MARKER_END) :].lstrip("\n")
        return before + section + after
    stripped = existing.rstrip("\n")
    prefix = stripped + "\n\n" if stripped else ""
    return prefix + section


def sync_instruction_file(
    path: Path,
    *,
    root: Path | None = None,
    check: bool = False,
) -> bool:
    """Write or update the uncoded navigation section in an instruction file.

    When ``check=True``, reports a prospective change without touching disk.
    Returns ``True`` if a write was (or would be) performed.

    When ``root`` is provided, ``path`` is resolved against ``root`` for
    filesystem I/O while the printed message remains ``path`` for
    project-relative display.
    """
    section = generate_section()
    target = root / path if root is not None else path
    if not target.exists():
        return sync_file(path, section, root=root, check=check)
    existing = target.read_text()
    updated = _replace_or_append(existing, section)
    return sync_file(path, updated, root=root, check=check)
