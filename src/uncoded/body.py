"""Retrieve the source body of a named symbol in a Python file."""

import ast
from pathlib import Path

from uncoded.read_helpers import read_source_text
from uncoded.resolver import NamePath, resolve_ast_node_from_source


def resolve_body(name_path: NamePath, in_path: Path) -> str:
    """Return the source text for the symbol named by name_path in in_path.

    Raises SymbolNotFound if the symbol is not present. Lets OSError,
    UnicodeDecodeError, and SyntaxError propagate from the file read.
    """
    source = read_source_text(in_path)
    node = resolve_ast_node_from_source(
        name_path=name_path, source=source, in_path=in_path
    )
    return _extract_body(node=node, lines=source.splitlines(keepends=True))


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
