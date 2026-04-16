"""Maintain the uncoded navigation section in CLAUDE.md."""

from pathlib import Path

MARKER_START = "<!-- uncoded:start -->"
MARKER_END = "<!-- uncoded:end -->"

DEFAULT_CLAUDE_MD = Path("CLAUDE.md")

_SECTION_BODY = """\
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
```"""

SECTION = f"{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n"


def generate_section() -> str:
    """Return the full delimited uncoded section for insertion into CLAUDE.md."""
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


def sync_claude_md(path: Path = DEFAULT_CLAUDE_MD) -> None:
    """Write or update the uncoded navigation section in CLAUDE.md."""
    section = generate_section()
    if not path.exists():
        path.write_text(section)
        print(f"Wrote {path}")
        return
    existing = path.read_text()
    updated = _replace_or_append(existing, section)
    if updated != existing:
        path.write_text(updated)
        print(f"Updated {path}")
