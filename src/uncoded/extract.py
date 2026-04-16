"""Extract public symbols from Python source files using the AST."""

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ClassInfo:
    """A public class with its public attributes and methods."""

    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Public symbols found in a single Python module."""

    rel_path: str
    constants: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)


# Dunders treated as public — conventional module-level public API.
_DUNDER_PUBLIC = frozenset({"__all__", "__version__"})


def is_public(name: str) -> bool:
    """A name is public if it has no leading underscore (or is a public dunder)."""
    if name in _DUNDER_PUBLIC:
        return True
    return not name.startswith("_")


def _property_kind(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Classify a method by its property-related decorators.

    Returns "property" for @property, "setter" for @<name>.setter,
    "deleter" for @<name>.deleter, or None for a plain method.
    """
    for d in node.decorator_list:
        if isinstance(d, ast.Name) and d.id == "property":
            return "property"
        if isinstance(d, ast.Attribute) and d.attr in ("setter", "deleter"):
            return d.attr
    return None


def _assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    """Return the single-name target of an assignment, or None if not a simple name."""
    if isinstance(node, ast.AnnAssign):
        target = node.target
        return target.id if isinstance(target, ast.Name) else None
    if len(node.targets) != 1:
        return None
    target = node.targets[0]
    return target.id if isinstance(target, ast.Name) else None


def extract_module(source: str, rel_path: str) -> ModuleInfo:
    """Parse Python source and extract public classes, functions, and constants."""
    tree = ast.parse(source)

    constants: list[str] = []
    classes: list[ClassInfo] = []
    functions: list[str] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and is_public(node.name):
            attributes: list[str] = []
            methods: list[str] = []
            for n in ast.iter_child_nodes(node):
                if isinstance(n, (ast.AnnAssign, ast.Assign)):
                    name = _assign_target_name(n)
                    if name and is_public(name):
                        attributes.append(name)
                elif isinstance(
                    n, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and is_public(n.name):
                    kind = _property_kind(n)
                    if kind == "setter" or kind == "deleter":
                        continue
                    if kind == "property":
                        attributes.append(n.name)
                    else:
                        methods.append(n.name)
            classes.append(
                ClassInfo(name=node.name, attributes=attributes, methods=methods)
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(
            node.name
        ):
            functions.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            name = _assign_target_name(node)
            if name and is_public(name):
                constants.append(name)
        elif isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
            if is_public(node.name.id):
                constants.append(node.name.id)

    return ModuleInfo(
        rel_path=rel_path,
        constants=constants,
        classes=classes,
        functions=functions,
    )


def iter_source_files(
    source_root: Path, base: Path | None = None
) -> Iterator[tuple[str, str]]:
    """Yield (source_text, rel_path) for each candidate Python file.

    Includes __init__.py when it contains public symbols. Skips other
    private modules (leading underscore) and private directories. Paths
    are relative to *base* (defaults to cwd).
    """
    if base is None:
        base = Path.cwd()

    source_root = source_root.resolve()
    base = base.resolve()

    for py_file in sorted(source_root.rglob("*.py")):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue

        try:
            rel_to_root = py_file.relative_to(source_root)
        except ValueError:
            continue
        if any(part.startswith("_") for part in rel_to_root.parts[:-1]):
            continue

        rel_path = str(py_file.relative_to(base))
        yield py_file.read_text(), rel_path


def walk_source(source_root: Path, base: Path | None = None) -> list[ModuleInfo]:
    """Walk a source root and extract public symbols from all packages.

    Paths in the returned ModuleInfo are relative to *base* (defaults to
    cwd), so they can be used directly to open files from the repo root.

    Includes __init__.py when it contains public symbols. Skips other
    private modules (leading underscore), files with no public symbols,
    and files with syntax errors.
    """
    modules: list[ModuleInfo] = []

    for source, rel_path in iter_source_files(source_root, base):
        try:
            module = extract_module(source, rel_path)
        except SyntaxError:
            continue

        if module.classes or module.functions or module.constants:
            modules.append(module)

    return modules
