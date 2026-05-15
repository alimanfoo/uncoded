"""AST helper functions shared across multiple uncoded modules."""

import ast


def property_kind(
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


def assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    """Return the single-name target of an assignment, or None if not a simple name."""
    if isinstance(node, ast.AnnAssign):
        target = node.target
        return target.id if isinstance(target, ast.Name) else None
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    return target.id if isinstance(target, ast.Name) else None
