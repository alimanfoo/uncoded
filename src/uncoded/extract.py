"""Extract symbols from Python source files using the AST."""

import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.ast_helpers import assign_target_name, property_kind
from uncoded.read_helpers import _read_file_text


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
                    name = assign_target_name(n)
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
            name = assign_target_name(node)
            if name:
                constants.append(name)
        elif isinstance(node, ast.TypeAlias):
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
    """Yield (source_text, rel_path) for every readable, parseable Python file.

    Each yielded ``rel_path`` is the file's path relative to
    ``project_root``.

    Source files are read as UTF-8; a file with a non-UTF-8 encoding (such
    as one declared with ``# -*- coding: latin-1 -*-``) is treated as
    unreadable and skipped. Files that fail to read (unreadable or non-UTF-8)
    or fail to parse are each skipped with a single ``warning: skipping ...``
    line on stderr — centralising these decisions here lets ``extract_modules``
    and ``_generate_stubs`` trust they only receive readable, parseable source.
    """
    source_root = source_root.resolve()
    project_root = project_root.resolve()

    for py_file in sorted(source_root.rglob("*.py")):
        rel_path = str(py_file.relative_to(project_root))
        source = _read_file_text(py_file, display=rel_path)
        if source is None:
            continue
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
