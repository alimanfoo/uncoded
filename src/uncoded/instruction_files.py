"""Maintain the uncoded navigation section in agent instruction files.

Different coding agents read different instruction files from a repo's root.
Claude Code reads ``CLAUDE.md``; an emerging cross-agent convention uses
``AGENTS.md``. Until the ecosystem converges, a project that wants to support
both populations needs both files, with the same navigation guidance in each.
Two configurations work: keep the two files as separate copies (sync writes
each), or symlink one to the other (sync dedupes by inode and writes once).
This module owns a delimited section in any such file and keeps it in sync.
"""

from importlib.resources import files
from pathlib import Path

from uncoded.sync import sync_file

MARKER_START = "<!-- uncoded:start -->"
MARKER_END = "<!-- uncoded:end -->"

DEFAULT_INSTRUCTION_FILES = [Path("CLAUDE.md"), Path("AGENTS.md")]

_SECTION_BODY = (
    (files("uncoded") / "dispatch_rule.md").read_text(encoding="utf-8").rstrip("\n")
)

SECTION = f"{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n"


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
    project_root: Path,
    check: bool = False,
) -> bool:
    """Write or update the uncoded navigation section in an instruction file.

    When ``check=True``, reports a prospective change without touching disk.
    Returns ``True`` if a write was (or would be) performed.

    The file is written to ``project_root / path``. The log line still
    names ``path`` as given, so messages stay project-relative
    regardless of where the caller is running from. If ``path`` is
    absolute, it's used as-is and ``project_root`` has no effect.
    """
    section = SECTION
    target = project_root / path
    if not target.exists():
        return sync_file(path, section, project_root=project_root, check=check)
    existing = target.read_text()
    updated = _replace_or_append(existing, section)
    return sync_file(path, updated, project_root=project_root, check=check)
