# src/uncoded/body.py

import ast
from pathlib import Path
from uncoded.read_helpers import read_source_text
from uncoded.resolver import NamePath, resolve_ast_node_from_source

def resolve_body(name_path: NamePath, in_path: Path) -> str:
    ...

def _extract_body(*, node: ast.stmt, lines: list[str]) -> str:
    ...
