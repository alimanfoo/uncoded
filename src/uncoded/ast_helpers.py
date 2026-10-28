"""AST helper functions shared across multiple uncoded modules."""

import ast
from collections.abc import Iterator


def property_kind(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Classify a function or method by its property-related decorators.

    Returns "property" for @property, "setter" for @<name>.setter,
    "deleter" for @<name>.deleter, or None for a plain function or method.
    """
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == "property":
            return "property"
        if isinstance(d, ast.Attribute) and d.attr in ("setter", "deleter"):
            return d.attr
    return None


def _assign_target_name(*, node: ast.Assign | ast.AnnAssign) -> str | None:
    """Return the single-name target of an assignment, or None if not a simple name."""
    if isinstance(node, ast.AnnAssign):
        target = node.target
        return target.id if isinstance(target, ast.Name) else None
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    return target.id if isinstance(target, ast.Name) else None


type SymbolNode = (
    ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.AnnAssign
    | ast.Assign
    | ast.TypeAlias
)

type _MemberNode = ast.FunctionDef | ast.AsyncFunctionDef | ast.AnnAssign | ast.Assign


def module_symbols(*, tree: ast.Module) -> Iterator[tuple[str, SymbolNode]]:
    """Yield the name and definition of each symbol in the module body, in order.

    A name defined more than once is yielded once for each definition.
    """
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name, node
        elif isinstance(node, ast.TypeAlias):
            yield node.name.id, node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            name = _assign_target_name(node=node)
            if name:
                yield name, node


def class_symbols(*, node: ast.ClassDef) -> Iterator[tuple[str, _MemberNode]]:
    """Yield the name and definition of each symbol in the class body, in order.

    A property's setter and deleter are not symbols. A name defined more than
    once is yielded once for each definition.
    """
    for child in node.body:
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            name = _assign_target_name(node=child)
            if name:
                yield name, child
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if property_kind(node=child) not in ("setter", "deleter"):
                yield child.name, child
