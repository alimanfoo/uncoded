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

        if module.classes or module.functions:
            modules.append(module)

    return modules
