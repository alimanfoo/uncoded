"""Build the docs map, in YAML, from Markdown files for agent orientation."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt

from uncoded.markers import GENERATED_MARKER
from uncoded.read_helpers import SkippedFile, failure_reason, root_files
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


@dataclass(frozen=True)
class DocFile:
    """A Markdown file's project-relative path and text."""

    rel_path: str
    text: str


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
    *, doc_roots: list[Path], project_directory: Path
) -> tuple[list[DocFile], list[SkippedFile]]:
    """Read the Markdown files of ``doc_roots``, keeping readable UTF-8 files.

    If a root is a directory, reads every Markdown file found by rglob, in
    sorted order. If it is a single Markdown file, reads just that file.
    Each file is read as UTF-8, and a leading UTF-8 BOM is stripped.

    Returns a :class:`DocFile` for every file that reads, and a
    :class:`SkippedFile` for every file that is unreadable or not UTF-8.
    Each ``rel_path`` is the file's path relative to ``project_directory``, with
    ``/`` separators on every platform.
    """
    files: list[DocFile] = []
    skipped: list[SkippedFile] = []
    for md_file, rel_path in root_files(
        roots=doc_roots, pattern="*.md", project_directory=project_directory
    ):
        try:
            text = md_file.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError) as e:
            skipped.append(SkippedFile(path=rel_path, reason=failure_reason(error=e)))
            continue
        files.append(DocFile(rel_path=rel_path, text=text))
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


def build_docs_map(*, files: Iterable[DocFile]) -> dict:
    """Build a nested dict from Markdown files.

    Top-level keys are directory names (trailing "/") and file names, and each
    file maps to its headings.
    """
    return nest_by_path(
        entries=(
            (doc_file.rel_path, _file_headings(text=doc_file.text))
            for doc_file in files
        )
    )


def render_docs_map(*, mapping: dict) -> str:
    """Render a docs map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(header=_DOCS_HEADER, mapping=mapping)
