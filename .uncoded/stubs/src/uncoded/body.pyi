# src/uncoded/body.py

import ast
from pathlib import Path
from typing import NamedTuple
from uncoded.ast_helpers import assign_target_name, property_kind

def parse_name_path(s: str) -> NamePath:
    ...

def resolve_ast_node(name_path: NamePath, in_path: Path) -> ast.stmt:
    ...

def resolve_name_position(name_path: NamePath, in_path: Path) -> tuple[int, int]:
    ...

def resolve_body(name_path: NamePath, in_path: Path) -> str:
    ...

def _resolve_ast_node_from_source(*, name_path: NamePath, source: str, in_path: Path) -> ast.stmt:
    ...

def _resolve_class_member(*, name_path: NamePath, in_path: Path, class_node: ast.ClassDef, member_name: str) -> ast.stmt:
    ...

def _extract_body(*, node: ast.stmt, lines: list[str]) -> str:
    ...

class NamePath(NamedTuple):
    head: str
    tail: str | None = None

    def __str__(self) -> str:
        ...

class SymbolNotFound(Exception):
    ...

class UnsupportedNamePath(Exception):
    ...
