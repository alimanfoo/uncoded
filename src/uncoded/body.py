"""Resolve the source body of a named symbol in a Python file."""

import ast
from pathlib import Path

from uncoded.ast_helpers import assign_target_name, property_kind


class BodyNotFound(Exception):
    """Raised when name_path cannot be found in the given file."""


def resolve_body(name_path: str, in_path: Path) -> str:
    """Return the source text for the symbol named by name_path in in_path.

    name_path is a slash-separated path: a single segment names a top-level
    symbol; two segments name a class member as Class/member (a method,
    property, or attribute).
    Raises BodyNotFound if the symbol is not present. Lets FileNotFoundError
    propagate if in_path does not exist, and SyntaxError if in_path cannot
    be parsed.
    """
    source = in_path.read_text()
    tree = ast.parse(source, filename=str(in_path))
    lines = source.splitlines(keepends=True)
    segments = name_path.split("/", maxsplit=1)
    head = segments[0]
    tail = segments[1] if len(segments) == 2 else None

    match: ast.stmt | None = None

    for node in ast.iter_child_nodes(tree):
        matches_class = isinstance(node, ast.ClassDef) and node.name == head
        matches_function = (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and tail is None
            and node.name == head
        )
        if matches_class or matches_function:
            match = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and tail is None:
            name = assign_target_name(node)
            if name == head:
                match = node
        elif isinstance(node, ast.TypeAlias) and tail is None and node.name.id == head:
            match = node

    if match is None:
        raise BodyNotFound(f"{name_path!r} not found in {in_path}")

    if tail is not None and isinstance(match, ast.ClassDef):
        return _resolve_class_member(
            name_path=name_path,
            in_path=in_path,
            class_node=match,
            member_name=tail,
            lines=lines,
        )

    return _extract_body(node=match, lines=lines)


def _resolve_class_member(
    *,
    name_path: str,
    in_path: Path,
    class_node: ast.ClassDef,
    member_name: str,
    lines: list[str],
) -> str:
    match: ast.stmt | None = None

    for node in ast.iter_child_nodes(class_node):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            name = assign_target_name(node)
            if name == member_name:
                match = node
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = property_kind(node)
            if kind in ("setter", "deleter"):
                continue
            if node.name == member_name:
                match = node

    if match is None:
        raise BodyNotFound(f"{name_path!r} not found in {in_path}")

    return _extract_body(node=match, lines=lines)


def _extract_body(*, node: ast.stmt, lines: list[str]) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if node.decorator_list:
            start = min(node.decorator_list[0].lineno, node.lineno)
        else:
            start = node.lineno
    else:
        start = node.lineno
    end = node.end_lineno
    return "".join(lines[start - 1 : end])
