"""Name-path resolution: parse, AST-walk, and position extraction."""

import ast
from pathlib import Path
from typing import NamedTuple

from uncoded.ast_helpers import assign_target_name, property_kind
from uncoded.read_helpers import read_source_text


class NamePath(NamedTuple):
    """A validated name path: one segment for top-level, two for Class/member."""

    head: str
    tail: str | None = None

    @classmethod
    def parse(cls, s: str) -> "NamePath":
        """Parse a raw name_path string into a validated NamePath.

        Raises UnsupportedNamePathError for more than two segments or any empty segment.
        """
        segments = s.split("/")
        if len(segments) > 2 or any(seg == "" for seg in segments):
            raise UnsupportedNamePathError(
                f"Unsupported name_path {s!r}: use 'name' or 'Class/member'"
            )
        head = segments[0]
        tail = segments[1] if len(segments) == 2 else None
        return cls(head=head, tail=tail)

    def __str__(self) -> str:
        """Return the string form: 'head/tail' when tail is set, 'head' otherwise."""
        return f"{self.head}/{self.tail}" if self.tail is not None else self.head


class SymbolNotFoundError(Exception):
    """Raised when name_path cannot be found in the given file."""


class UnsupportedNamePathError(Exception):
    """Raised when name_path does not match a supported shape.

    Supported shapes are 'name' (one segment) or 'Class/member' (two segments),
    both non-empty.
    """


def resolve_ast_node(name_path: NamePath, in_path: Path) -> ast.stmt:
    """Return the ast.stmt for the symbol named by name_path in in_path.

    Raises SymbolNotFoundError if the symbol is not present. Lets OSError,
    UnicodeDecodeError, and SyntaxError propagate from the file read.
    """
    source = read_source_text(in_path)
    return resolve_ast_node_from_source(
        name_path=name_path, source=source, in_path=in_path
    )


def resolve_name_position(name_path: NamePath, in_path: Path) -> tuple[int, int]:
    """Return the 0-indexed (line, character) position of the name token for name_path.

    Follows LSP convention: both line and character are 0-indexed.
    For def/async def/class, character points past the keyword to the identifier.
    For assignments and type aliases, character points at the start of the target name.
    Raises SymbolNotFoundError, OSError, UnicodeDecodeError, and SyntaxError under
    the same conditions as resolve_ast_node.
    """
    node = resolve_ast_node(name_path, in_path)
    if isinstance(node, ast.FunctionDef):
        return (node.lineno - 1, node.col_offset + len("def "))
    if isinstance(node, ast.AsyncFunctionDef):
        return (node.lineno - 1, node.col_offset + len("async def "))
    if isinstance(node, ast.ClassDef):
        return (node.lineno - 1, node.col_offset + len("class "))
    if isinstance(node, ast.AnnAssign):
        return (node.target.lineno - 1, node.target.col_offset)
    if isinstance(node, ast.Assign):
        return (node.targets[0].lineno - 1, node.targets[0].col_offset)
    if isinstance(node, ast.TypeAlias):
        return (node.name.lineno - 1, node.name.col_offset)
    node_type = type(node).__name__
    raise UnsupportedNamePathError(
        f"Cannot extract name position from {node_type} for {str(name_path)!r}"
    )


def resolve_ast_node_from_source(
    *,
    name_path: NamePath,
    source: str,
    in_path: Path,
) -> ast.stmt:
    """Return the ast.stmt for name_path given an already-read source string.

    The primitive that lets resolve_ast_node and resolve_body share a single
    file read. Callers that already have the source string call this directly
    to avoid reading in_path again. in_path is used only for ast.parse's
    filename argument and for error messages.
    Raises SymbolNotFoundError if the symbol is not present; propagates SyntaxError
    if source cannot be parsed.
    """
    tree = ast.parse(source, filename=str(in_path))
    head = name_path.head
    tail = name_path.tail

    top_match: ast.stmt | None = None

    for node in ast.iter_child_nodes(tree):
        matches_class = isinstance(node, ast.ClassDef) and node.name == head
        matches_function = (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and tail is None
            and node.name == head
        )
        if matches_class or matches_function:
            top_match = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and tail is None:
            name = assign_target_name(node)
            if name == head:
                top_match = node
        elif isinstance(node, ast.TypeAlias) and tail is None and node.name.id == head:
            top_match = node

    if top_match is None:
        raise SymbolNotFoundError(f"{str(name_path)!r} not found in {in_path}")

    if tail is not None and isinstance(top_match, ast.ClassDef):
        return _resolve_class_member(
            name_path=name_path,
            in_path=in_path,
            class_node=top_match,
            member_name=tail,
        )

    return top_match


def _resolve_class_member(
    *,
    name_path: NamePath,
    in_path: Path,
    class_node: ast.ClassDef,
    member_name: str,
) -> ast.stmt:
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
        raise SymbolNotFoundError(f"{str(name_path)!r} not found in {in_path}")

    return match
