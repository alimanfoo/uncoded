# src/uncoded/body.py

import ast
from pathlib import Path
from uncoded.ast_helpers import assign_target_name, property_kind

def resolve_body(name_path: str, in_path: Path) -> str:
    ...

def _resolve_class_member(*, name_path: str, in_path: Path, class_node: ast.ClassDef, member_name: str, lines: list[str]) -> str:
    ...

def _extract_body(*, node: ast.stmt, lines: list[str]) -> str:
    ...

class BodyNotFound(Exception):
    ...
