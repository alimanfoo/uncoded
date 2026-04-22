"""Maintain the uncoded navigation section in agent instruction files.

Different coding agents read different instruction files from a repo's root.
Claude Code reads ``CLAUDE.md``; an emerging cross-agent convention uses
``AGENTS.md``. Until the ecosystem converges, a project that wants to support
both populations needs both files, with the same navigation guidance in each.
This module owns a delimited section in any such file and keeps it in sync.
"""

from pathlib import Path

from uncoded.sync import sync_file

MARKER_START = "<!-- uncoded:start -->"
MARKER_END = "<!-- uncoded:end -->"

DEFAULT_INSTRUCTION_FILES = [Path("CLAUDE.md"), Path("AGENTS.md")]

_SECTION_BODY = """\
## How to navigate this codebase and read source files

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
reading."""

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


def sync_instruction_file(path: Path, *, check: bool = False) -> bool:
    """Write or update the uncoded navigation section in an instruction file.

    When ``check=True``, reports a prospective change without touching disk.
    Returns ``True`` if a write was (or would be) performed.
    """
    section = generate_section()
    if not path.exists():
        return sync_file(path, section, check=check)
    existing = path.read_text()
    updated = _replace_or_append(existing, section)
    return sync_file(path, updated, check=check)
