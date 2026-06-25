"""Build a YAML doc map from Markdown files for agent orientation."""

from collections.abc import Iterable, Iterator
from pathlib import Path

from uncoded.markers import GENERATED_MARKER
from uncoded.read_helpers import read_doc_text_or_warn
from uncoded.yaml_tree import render_yaml_tree

DOCS_HEADER = f"""\
# Documentation index of this codebase, for agent orientation.
# {GENERATED_MARKER}
#
# Pure key hierarchy (no lists, no values); indent to zoom in.
# Directory keys end with "/". Leaf headings map to null.
#
# A " (N)" suffix marks the Nth occurrence of a repeated heading at that level.
# To navigate to it, grep the base heading text and take the Nth match.
"""


def _parse_atx_heading(line: str) -> tuple[int, str] | None:
    if not line.startswith("#"):
        return None
    # Count consecutive leading #.
    level = 0
    while level < len(line) and line[level] == "#":
        level += 1
    # Valid ATX: 1-6 # followed by exactly one space.
    if level > 6 or level >= len(line) or line[level] != " ":
        return None
    title = line[level + 1 :].strip()
    # Strip a trailing # run only when it is a CommonMark closing
    # sequence: preceded by whitespace, or the title is entirely #s.
    if title.endswith("#"):
        stripped = title.rstrip("#")
        if not stripped or stripped[-1] in " \t":
            title = stripped.rstrip()
    return (level, title) if title else None


def extract_headings(text: str) -> list[tuple[int, str]]:
    """Return the ATX headings in ``text`` as ordered (level, title) pairs.

    Recognises ATX headings only: 1-6 ``#`` followed by a space and a
    non-empty title. A trailing ``#`` run is stripped only when it forms
    a CommonMark closing sequence — preceded by whitespace, or the title
    consists entirely of ``#`` characters. A ``#`` attached to the final
    word (e.g. ``C#``) is preserved. Lines inside fenced code blocks
    (opened by a line starting with ```` ``` ```` or ``~~~``, closed by
    the matching marker) are not headings. Setext underlines are never
    recognised.

    Corners not in the criterion:
    - Indented headings: the ``#`` must be at column 0; leading spaces
      are not stripped.
    - Fence lengths: fences are matched by their first three characters
      (````` ``` ````` or ``~~~``), regardless of the exact number of
      backticks or tildes.
    """
    headings: list[tuple[int, str]] = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        if in_fence:
            if line.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue

        if line.startswith(("```", "~~~")):
            in_fence = True
            fence_marker = line[:3]
            continue

        result = _parse_atx_heading(line)
        if result is not None:
            headings.append(result)

    return headings


def _unique_key(*, parent: dict, title: str) -> str:
    """Return title, or a ` (n)` suffixed variant if title already exists."""
    if title not in parent:
        return title
    n = 2
    while f"{title} ({n})" in parent:
        n += 1
    return f"{title} ({n})"


def _collapse_empty(*, mapping: dict) -> dict | None:
    """Recursively replace empty dicts with None (leaf headings map to null)."""
    if not mapping:
        return None
    return {k: _collapse_empty(mapping=v) for k, v in mapping.items()}


def iter_doc_files(doc_root: Path, project_root: Path) -> Iterator[tuple[str, Path]]:
    """Yield (text, rel_path) for .md files under ``doc_root``.

    If ``doc_root`` is a directory, yields all ``*.md`` files found by
    rglob in sorted order. If it is a single ``.md`` file, yields just
    that file. ``rel_path`` is relative to ``project_root``.

    Files that fail to read (unreadable or non-UTF-8) are skipped with a
    one-line warning to stderr and do not abort the iteration.
    """
    doc_root = doc_root.resolve()
    project_root = project_root.resolve()
    if doc_root.is_file():
        rel = doc_root.relative_to(project_root)
        text = read_doc_text_or_warn(doc_root, warning_path=rel)
        if text is not None:
            yield text, rel
    else:
        for md_file in sorted(doc_root.rglob("*.md")):
            rel = md_file.relative_to(project_root)
            text = read_doc_text_or_warn(md_file, warning_path=rel)
            if text is None:
                continue
            yield text, rel


def build_docs_map(files: Iterable[tuple[str, Path]]) -> dict:
    """Build a nested dict from ``(text, rel_path)`` doc-file pairs.

    Top-level keys are directory names (trailing "/") and file names.
    Headings nest under the nearest preceding heading of a smaller level;
    level skips attach to the nearest shallower heading. Duplicate sibling
    headings are disambiguated with " (2)", " (3)", … A file with no
    headings maps to null.
    """
    root: dict = {}

    for text, rel_path in files:
        parts = rel_path.parts
        current = root

        for dir_part in parts[:-1]:
            dir_key = dir_part + "/"
            if dir_key not in current:
                current[dir_key] = {}
            current = current[dir_key]

        file_dict: dict = {}
        # Stack of (level, children_dict) — the active path from file root.
        stack: list[tuple[int, dict]] = [(0, file_dict)]

        for level, title in extract_headings(text):
            while stack[-1][0] >= level:
                stack.pop()
            parent_dict = stack[-1][1]
            key = _unique_key(parent=parent_dict, title=title)
            heading_dict: dict = {}
            parent_dict[key] = heading_dict
            stack.append((level, heading_dict))

        current[parts[-1]] = _collapse_empty(mapping=file_dict)

    return root


def render_docs_map(mapping: dict) -> str:
    """Render a docs map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(DOCS_HEADER, mapping)
