"""Maintain uncoded navigation sections in agent instruction files.

Different coding agents read different instruction files from a repo's root.
Claude Code reads ``CLAUDE.md``; an emerging cross-agent convention uses
``AGENTS.md``. Until the ecosystem converges, a project that wants to support
both populations needs both files, with the same navigation guidance in each.
Two configurations work: keep the two files as separate copies (sync writes
each), or symlink one to the other (sync dedupes by inode and writes once).
This module owns delimited sections in any such file and keeps them in sync.
"""

from importlib.resources import files
from pathlib import Path

from uncoded.sync import sync_file

MARKER_START = "<!-- uncoded:start -->"
MARKER_END = "<!-- uncoded:end -->"
MARKER_DOCS_START = "<!-- uncoded:docs:start -->"
MARKER_DOCS_END = "<!-- uncoded:docs:end -->"

DEFAULT_INSTRUCTION_FILES = [Path("CLAUDE.md"), Path("AGENTS.md")]

_CODE_SECTION_BODY = (
    (files("uncoded") / "dispatch_rule.md").read_text(encoding="utf-8").rstrip("\n")
)
SECTION_CODE = f"{MARKER_START}\n{_CODE_SECTION_BODY}\n{MARKER_END}\n"

_DOCS_SECTION_BODY = (
    (files("uncoded") / "docs_rule.md").read_text(encoding="utf-8").rstrip("\n")
)
SECTION_DOCS = f"{MARKER_DOCS_START}\n{_DOCS_SECTION_BODY}\n{MARKER_DOCS_END}\n"


def _apply_section(text: str, start: str, end: str, body: str | None) -> str:
    """Apply, replace, or remove the delimited section in text.

    When body is a string: replaces the section if already present,
    appends it otherwise. When body is None: removes the section if
    present, leaves text unchanged otherwise.
    """
    s = text.find(start)
    e = text.find(end)
    section_found = s != -1 and e != -1 and s < e

    if body is None:
        if not section_found:
            return text
        before = text[:s]
        after = text[e + len(end) :].lstrip("\n")
        return before + after
    else:
        if section_found:
            before = text[:s]
            after = text[e + len(end) :].lstrip("\n")
            return before + body + after
        else:
            stripped = text.rstrip("\n")
            prefix = stripped + "\n\n" if stripped else ""
            return prefix + body


def sync_instruction_file(
    path: Path,
    *,
    code_section: str | None,
    docs_section: str | None,
    project_root: Path,
    check: bool = False,
) -> bool:
    """Write or update the uncoded navigation sections in an instruction file.

    Applies the code-navigation section (code_section) and the
    docs-navigation section (docs_section) in that order. Passing None
    for a section removes it if present. When both are None and the file
    does not yet exist, returns False without touching disk.

    When ``check=True``, reports a prospective change without touching
    disk. Returns ``True`` if a write was (or would be) performed.

    The file is written to ``project_root / path``. The log line still
    names ``path`` as given, so messages stay project-relative
    regardless of where the caller is running from.
    """
    target = project_root / path
    if not target.exists() and code_section is None and docs_section is None:
        return False
    existing = target.read_text() if target.exists() else ""
    updated = _apply_section(existing, MARKER_START, MARKER_END, code_section)
    updated = _apply_section(updated, MARKER_DOCS_START, MARKER_DOCS_END, docs_section)
    return sync_file(path, updated, project_root=project_root, check=check)
