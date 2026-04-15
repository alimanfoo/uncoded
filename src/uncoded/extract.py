"""Extract public symbols from Python source files using the AST."""

import ast
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
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)


def is_public(name: str) -> bool:
    """A name is public if it has no leading underscore."""
    return not name.startswith("_")


def extract_module(source: str, rel_path: str) -> ModuleInfo:
    """Parse Python source and extract public classes and functions."""
    tree = ast.parse(source)

    classes: list[ClassInfo] = []
    functions: list[str] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and is_public(node.name):
            attributes = [
                n.target.id
                for n in ast.iter_child_nodes(node)
                if isinstance(n, ast.AnnAssign)
                and isinstance(n.target, ast.Name)
                and is_public(n.target.id)
            ]
            methods = [
                n.name
                for n in ast.iter_child_nodes(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and is_public(n.name)
            ]
            classes.append(
                ClassInfo(name=node.name, attributes=attributes, methods=methods)
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(
            node.name
        ):
            functions.append(node.name)

    return ModuleInfo(rel_path=rel_path, classes=classes, functions=functions)


def walk_source(source_root: Path, base: Path | None = None) -> list[ModuleInfo]:
    """Walk a source root and extract public symbols from all packages.

    Paths in the returned ModuleInfo are relative to *base* (defaults to
    cwd), so they can be used directly to open files from the repo root.

    Skips __init__.py, private modules (leading underscore), and files
    that contain no public symbols. Skips files with syntax errors.
    """
    if base is None:
        base = Path.cwd()

    source_root = source_root.resolve()
    base = base.resolve()
    modules: list[ModuleInfo] = []

    for py_file in sorted(source_root.rglob("*.py")):
        # Skip private modules and __init__.py
        if py_file.name.startswith("_"):
            continue

        # Skip if any parent directory (within source root) is private
        try:
            rel_to_root = py_file.relative_to(source_root)
        except ValueError:
            continue
        if any(part.startswith("_") for part in rel_to_root.parts[:-1]):
            continue

        # Path relative to base (repo root), for use in the map
        rel_path = str(py_file.relative_to(base))

        source = py_file.read_text()

        try:
            module = extract_module(source, rel_path)
        except SyntaxError:
            continue

        if module.classes or module.functions:
            modules.append(module)

    return modules
