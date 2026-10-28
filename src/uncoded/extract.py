"""Extract symbols from Python source files using the AST."""

import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.ast_helpers import (
    assign_target_name,
    property_kind,
    top_level_definitions,
)
from uncoded.read_helpers import SkippedFile, failure_reason, read_source_text


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


def _extract_class_members(*, node: ast.ClassDef) -> ClassInfo:
    attributes: list[str] = []
    methods: list[str] = []
    for n in ast.iter_child_nodes(node):
        if isinstance(n, (ast.AnnAssign, ast.Assign)):
            name = assign_target_name(node=n)
            if name:
                attributes.append(name)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = property_kind(node=n)
            if kind in {"setter", "deleter"}:
                continue
            if kind == "property":
                attributes.append(n.name)
            else:
                methods.append(n.name)
    return ClassInfo(name=node.name, attributes=attributes, methods=methods)


def extract_module(*, source: str, rel_path: str) -> ModuleInfo:
    """Parse Python source and extract classes, functions, and constants.

    A name defined more than once keeps only its later definition.
    """
    tree = ast.parse(source)

    constants: list[str] = []
    classes: list[ClassInfo] = []
    functions: list[str] = []

    for name, node in top_level_definitions(tree=tree).items():
        if isinstance(node, ast.ClassDef):
            classes.append(_extract_class_members(node=node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(name)
        else:
            constants.append(name)

    return ModuleInfo(
        rel_path=rel_path,
        constants=constants,
        classes=classes,
        functions=functions,
    )


def read_source_files(
    *, source_root: Path, project_root: Path
) -> tuple[list[tuple[str, str]], list[SkippedFile]]:
    """Read every Python file under ``source_root``, keeping those that parse.

    Returns the ``(source_text, rel_path)`` pair of every readable, parseable
    file, and a :class:`SkippedFile` for every other one. Each ``rel_path`` is
    the file's path relative to ``project_root``.

    Source files are read under their declared PEP 263 encoding, UTF-8
    default. A file is skipped when it fails to read (OSError,
    UnicodeDecodeError, or a SyntaxError from a malformed encoding cookie) or
    fails to parse (SyntaxError). Deciding this here lets ``extract_modules``
    and ``_generate_stubs`` trust they only receive readable, parseable source.
    """
    source_root = source_root.resolve()
    project_root = project_root.resolve()

    files: list[tuple[str, str]] = []
    skipped: list[SkippedFile] = []
    for py_file in sorted(source_root.rglob("*.py")):
        rel_path = py_file.relative_to(project_root).as_posix()
        try:
            source = read_source_text(path=py_file)
        except (OSError, UnicodeDecodeError, SyntaxError) as e:
            skipped.append(SkippedFile(path=rel_path, reason=failure_reason(error=e)))
            continue
        try:
            ast.parse(source, rel_path)
        except SyntaxError as e:
            reason = f"SyntaxError at line {e.lineno}: {e.msg}"
            skipped.append(SkippedFile(path=rel_path, reason=reason))
            continue
        files.append((source, rel_path))
    return files, skipped


def extract_modules(*, files: Iterable[tuple[str, str]]) -> list[ModuleInfo]:
    """Extract a :class:`ModuleInfo` for each file in *files*.

    *files* holds the readable files from :func:`read_source_files`, as
    ``(source, rel_path)`` pairs where the source has already been
    confirmed parseable. Pure transformation: no IO, no warnings, no
    parsing decisions. Skips files with no symbols.
    """
    modules: list[ModuleInfo] = []
    for source, rel_path in files:
        module = extract_module(source=source, rel_path=rel_path)
        if module.classes or module.functions or module.constants:
            modules.append(module)
    return modules
