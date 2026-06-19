"""Maintain uncoded navigation sections in agent instruction files.

Different coding agents read different instruction files from a repo's root.
Claude Code reads ``CLAUDE.md``; an emerging cross-agent convention uses
``AGENTS.md``. Until the ecosystem converges, a project that wants to support
both populations needs both files, with the same navigation guidance in each.
Two configurations work: keep the two files as separate copies (sync writes
each), or symlink one to the other (sync dedupes by inode and writes once).
This module owns delimited sections in any such file and keeps them in sync.
"""

import hashlib
from importlib.resources import files
from pathlib import Path

from uncoded.sync import sync_file

MARKER_END = "<!-- uncoded:end -->"
MARKER_DOCS_END = "<!-- uncoded:docs:end -->"
MARKER_START_PREFIX = "<!-- uncoded:start"
MARKER_DOCS_START_PREFIX = "<!-- uncoded:docs:start"

DEFAULT_INSTRUCTION_FILES = [Path("CLAUDE.md"), Path("AGENTS.md")]

# The opening markers carry a short sha256 stamp of uncoded's canonical
# section body, computed once at module load. On sync, the on-disk
# opening-marker line is compared to the canonical marker: a matching stamp
# means this version's wording is already planted, so the body is left alone
# and a formatter's reflow survives; a differing stamp means the wording
# changed (e.g. on upgrade) and the whole section is replaced.
_CODE_SECTION_BODY = (
    (files("uncoded") / "dispatch_rule.md").read_text(encoding="utf-8").rstrip("\n")
)
MARKER_START = (
    f"{MARKER_START_PREFIX} sha256="
    f"{hashlib.sha256(_CODE_SECTION_BODY.encode()).hexdigest()[:8]} -->"
)
SECTION_CODE = f"{MARKER_START}\n{_CODE_SECTION_BODY}\n{MARKER_END}\n"

_DOCS_SECTION_BODY = (
    (files("uncoded") / "docs_rule.md").read_text(encoding="utf-8").rstrip("\n")
)
MARKER_DOCS_START = (
    f"{MARKER_DOCS_START_PREFIX} sha256="
    f"{hashlib.sha256(_DOCS_SECTION_BODY.encode()).hexdigest()[:8]} -->"
)
SECTION_DOCS = f"{MARKER_DOCS_START}\n{_DOCS_SECTION_BODY}\n{MARKER_DOCS_END}\n"


def _apply_section(
    text: str, start: str, end: str, body: str | None, *, prefix: str
) -> str:
    """Apply, replace, or remove the delimited section in text.

    Applying this function twice produces the same result as applying it once,
    and no text outside the uncoded markers is ever deleted.

    Scans lines to anchor both the opening and closing markers to line starts.
    The first line whose content (trailing \\r\\n stripped) starts with prefix
    is the opening; the first line after it whose stripped content equals end
    is the closing. This prevents marker-like prose from being mistaken for a
    boundary, and prevents an end marker before any start from acting as the
    closing.

    CRLF: marker lines are compared with trailing \\r stripped; the canonical
    section is written with \\n; surrounding content is preserved byte-for-byte.
    A CRLF file converges in one pass.

    Duplicate policy: the first well-formed section (a start-prefix line through
    its matching end line) is managed; any additional well-formed uncoded section
    is collapsed to leave at most one. A lone orphan marker (a start with no
    later end, or an end with no earlier start) is left untouched.

    Stamp tolerance: when the located opening line's content matches start, the
    body is left byte-for-byte (a formatter's reflow survives); when it differs,
    the whole section is replaced.

    When body is a string:
    - absent → append the canonical section;
    - found and opening-marker line matches start → managed section preserved
      byte-for-byte; any extra copies collapsed;
    - found and opening-marker line differs → replace with the canonical section.
    When body is None: remove the section and any extra copies if present.
    """
    lines = text.splitlines(keepends=True)

    # Single pass: find the first complete section (managed) and any extras.
    # States: "before", "in_first", "after", "in_extra".
    managed: tuple[int, int] | None = None  # inclusive line indices
    extras: list[tuple[int, int]] = []
    state = "before"
    current_start = 0

    for i, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        if state == "before":
            if stripped.startswith(prefix):
                current_start = i
                state = "in_first"
        elif state == "in_first":
            if stripped == end:
                managed = (current_start, i)
                state = "after"
        elif state == "after":
            if stripped.startswith(prefix):
                current_start = i
                state = "in_extra"
        else:  # "in_extra"
            if stripped == end:
                extras.append((current_start, i))
                state = "after"

    if managed is None:
        if body is None:
            return text
        if state == "in_first":
            # Lone start orphan with no matching end: insert the section before
            # the orphan so the section is found first on the next pass and the
            # orphan is preserved byte-for-byte (no prose deleted).
            text_before_orphan = "".join(lines[:current_start])
            orphan_and_after = "".join(lines[current_start:])
            stripped_before = text_before_orphan.rstrip("\n")
            lead = stripped_before + "\n\n" if stripped_before else ""
            return lead + body + orphan_and_after
        stripped_text = text.rstrip("\n")
        lead = stripped_text + "\n\n" if stripped_text else ""
        return lead + body

    extra_drop: set[int] = set()
    for lo, hi in extras:
        extra_drop.update(range(lo, hi + 1))

    before = "".join(lines[: managed[0]])
    after = "".join(
        ln
        for i, ln in enumerate(lines[managed[1] + 1 :], start=managed[1] + 1)
        if i not in extra_drop
    ).lstrip("\n")

    if body is None:
        return before + after

    opening_line = lines[managed[0]].rstrip("\r\n")
    if opening_line == start:
        if not extras:
            return text
        original_section = "".join(lines[managed[0] : managed[1] + 1])
        return before + original_section + after

    return before + body + after


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
    updated = _apply_section(
        existing,
        MARKER_START,
        MARKER_END,
        code_section,
        prefix=MARKER_START_PREFIX,
    )
    updated = _apply_section(
        updated,
        MARKER_DOCS_START,
        MARKER_DOCS_END,
        docs_section,
        prefix=MARKER_DOCS_START_PREFIX,
    )
    return sync_file(path, updated, project_root=project_root, check=check)
