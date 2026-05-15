# src/uncoded/ast_helpers.py

import ast

def property_kind(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    ...

def assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    ...
