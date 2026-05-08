"""Extract symbols from Python source files using the AST."""

import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ClassInfo:
    """A class with its attributes and methods."""

    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Symbols found in a single Python module."""

    rel_path: str
    constants: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)


def property_kind(
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
    """Parse Python source and extract classes, functions, and constants."""
    tree = ast.parse(source)

    constants: list[str] = []
    classes: list[ClassInfo] = []
    functions: list[str] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            attributes: list[str] = []
            methods: list[str] = []
            for n in ast.iter_child_nodes(node):
                if isinstance(n, (ast.AnnAssign, ast.Assign)):
                    name = _assign_target_name(n)
                    if name:
                        attributes.append(name)
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = property_kind(n)
                    if kind == "setter" or kind == "deleter":
                        continue
                    if kind == "property":
                        attributes.append(n.name)
                    else:
                        methods.append(n.name)
            classes.append(
                ClassInfo(name=node.name, attributes=attributes, methods=methods)
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            name = _assign_target_name(node)
            if name:
                constants.append(name)
        elif isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
            constants.append(node.name.id)

    return ModuleInfo(
        rel_path=rel_path,
        constants=constants,
        classes=classes,
        functions=functions,
    )


def iter_source_files(
    source_root: Path, project_root: Path
) -> Iterator[tuple[str, str]]:
    """Yield (source_text, rel_path) for every parseable Python file in *source_root*.

    Each yielded ``rel_path`` is the file's path relative to
    ``project_root``.

    Files that fail to parse are skipped with a single ``warning:
    skipping ...`` line on stderr — centralising the syntax-error
    decision here lets ``extract_modules`` and ``_generate_stubs``
    trust they only receive parseable source.
    """
    source_root = source_root.resolve()
    project_root = project_root.resolve()

    for py_file in sorted(source_root.rglob("*.py")):
        rel_path = str(py_file.relative_to(project_root))
        source = py_file.read_text()
        try:
            ast.parse(source, rel_path)
        except SyntaxError as e:
            print(
                f"warning: skipping {rel_path}: "
                f"SyntaxError at line {e.lineno}: {e.msg}",
                file=sys.stderr,
            )
            continue
        yield source, rel_path


def extract_modules(files: Iterable[tuple[str, str]]) -> list[ModuleInfo]:
    """Extract a :class:`ModuleInfo` for each file in *files*.

    *files* is the output of :func:`iter_source_files` — an iterable of
    ``(source, rel_path)`` pairs where the source has already been
    confirmed parseable. Pure transformation: no IO, no warnings, no
    parsing decisions. Skips files with no symbols.
    """
    modules: list[ModuleInfo] = []
    for source, rel_path in files:
        module = extract_module(source, rel_path)
        if module.classes or module.functions or module.constants:
            modules.append(module)
    return modules


def walk_source(source_root: Path, project_root: Path) -> list[ModuleInfo]:
    """Walk a source root and extract symbols from all Python files.

    Each returned ``ModuleInfo.rel_path`` is the file's path relative
    to ``project_root``.

    Convenience wrapper around :func:`iter_source_files` and
    :func:`extract_modules`. Files with syntax errors are filtered out
    by ``iter_source_files`` (which emits a stderr warning naming the
    offending file).
    """
    return extract_modules(iter_source_files(source_root, project_root))
