"""Build the docs map, in YAML, from Markdown files for agent orientation."""

from collections.abc import Iterable
from pathlib import Path

from markdown_it import MarkdownIt

from uncoded.markers import GENERATED_MARKER
from uncoded.read_helpers import SkippedFile, failure_reason
from uncoded.yaml_tree import nest_by_path, render_yaml_tree

_DOCS_HEADER = f"""\
# Documentation index of this codebase, for agent orientation.
# {GENERATED_MARKER}
#
# Pure key hierarchy (no lists, no values); indent to zoom in.
# Directory keys end with "/". Leaf headings map to null.
#
# A " (N)" suffix marks the Nth heading with the same text under one
# parent. The suffix is not in the file: read the parent's section to find it.
"""


def _extract_headings(*, text: str) -> list[tuple[int, str]]:
    """Return non-empty CommonMark ATX headings as (level, title) pairs."""
    headings: list[tuple[int, str]] = []
    tokens = MarkdownIt("commonmark").parse(text)
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or set(token.markup) != {"#"}:
            continue
        title = tokens[index + 1].content
        if title:
            headings.append((int(token.tag[1:]), title))

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


def read_doc_files(
    *, doc_root: Path, project_directory: Path
) -> tuple[list[tuple[str, str]], list[SkippedFile]]:
    """Read the Markdown files of ``doc_root``, keeping those that read as UTF-8.

    If ``doc_root`` is a directory, reads every ``*.md`` file found by rglob,
    in sorted order. If it is a single ``.md`` file, reads just that file.
    Each file is read as UTF-8, and a leading UTF-8 BOM is stripped.

    Returns the ``(text, rel_path)`` pair of every file that reads, and a
    :class:`SkippedFile` for every file that is unreadable or not UTF-8.
    Each ``rel_path`` is the file's path relative to ``project_directory``, with
    ``/`` separators on every platform.
    """
    doc_root = doc_root.resolve()
    project_directory = project_directory.resolve()
    md_files = [doc_root] if doc_root.is_file() else sorted(doc_root.rglob("*.md"))

    files: list[tuple[str, str]] = []
    skipped: list[SkippedFile] = []
    for md_file in md_files:
        rel_path = md_file.relative_to(project_directory).as_posix()
        try:
            text = md_file.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError) as e:
            skipped.append(SkippedFile(path=rel_path, reason=failure_reason(error=e)))
            continue
        files.append((text, rel_path))
    return files, skipped


def _file_headings(*, text: str) -> dict | None:
    """Return the docs map entry of a Markdown file's ``text``: its headings.

    Headings nest under the nearest preceding heading of a smaller level;
    level skips attach to the nearest shallower heading. Duplicate sibling
    headings are disambiguated with " (2)", " (3)", … A file with no
    headings maps to None.
    """
    file_dict: dict = {}
    # Stack of (level, children_dict) — the active path from file root.
    stack: list[tuple[int, dict]] = [(0, file_dict)]

    for level, title in _extract_headings(text=text):
        while stack[-1][0] >= level:
            stack.pop()
        parent_dict = stack[-1][1]
        key = _unique_key(parent=parent_dict, title=title)
        heading_dict: dict = {}
        parent_dict[key] = heading_dict
        stack.append((level, heading_dict))

    return _collapse_empty(mapping=file_dict)


def build_docs_map(*, files: Iterable[tuple[str, str]]) -> dict:
    """Build a nested dict from ``(text, rel_path)`` doc-file pairs.

    Top-level keys are directory names (trailing "/") and file names, and each
    file maps to its headings.
    """
    return nest_by_path(
        entries=((rel_path, _file_headings(text=text)) for text, rel_path in files)
    )


def render_docs_map(*, mapping: dict) -> str:
    """Render a docs map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(header=_DOCS_HEADER, mapping=mapping)
