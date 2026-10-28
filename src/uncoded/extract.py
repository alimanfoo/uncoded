"""Extract symbols from Python source files using the AST."""

import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.ast_helpers import property_kind
from uncoded.read_helpers import SkippedFile, failure_reason, read_source_text


@dataclass
class Parameter:
    """A function parameter with its name and any annotation.

    ``/`` and ``*`` stand for the separators before keyword-only and after
    positional-only parameters.
    """

    name: str
    annotation: str | None = None


@dataclass
class FunctionSymbol:
    """A function or method with its signature."""

    name: str
    params: list[Parameter] = field(default_factory=list)
    return_annotation: str | None = None
    is_async: bool = False


@dataclass
class AssignmentSymbol:
    """An assignment or annotation whose one target is a bare name, or a property.

    ``value`` is the source of the right-hand side, or None when there is none,
    as for a bare annotation ``X: int`` or a property.
    """

    name: str
    annotation: str | None = None
    value: str | None = None


@dataclass
class TypeAliasSymbol:
    """A ``type`` statement, with the source of its value."""

    name: str
    value: str


@dataclass
class ClassSymbol:
    """A class with its bases and every definition in its class body."""

    name: str
    bases: list[str] = field(default_factory=list)
    attributes: list[AssignmentSymbol] = field(default_factory=list)
    methods: list[FunctionSymbol] = field(default_factory=list)


type Symbol = AssignmentSymbol | TypeAliasSymbol | ClassSymbol | FunctionSymbol


@dataclass
class PythonFile:
    """A Python file's imports and every definition in its module body.

    ``symbols`` keeps source order and every definition of a redefined name.
    """

    rel_path: str
    imports: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)

    @property
    def assignments(self) -> list[AssignmentSymbol | TypeAliasSymbol]:
        """The assignments, annotations and ``type`` statements, in order."""
        return [
            s
            for s in self.symbols
            if isinstance(s, (AssignmentSymbol, TypeAliasSymbol))
        ]

    @property
    def classes(self) -> list[ClassSymbol]:
        """The classes, in order."""
        return [s for s in self.symbols if isinstance(s, ClassSymbol)]

    @property
    def functions(self) -> list[FunctionSymbol]:
        """The functions, in order."""
        return [s for s in self.symbols if isinstance(s, FunctionSymbol)]


def _unparse_or_none(*, node: ast.expr | None) -> str | None:
    """Unparse an optional annotation node, returning None when absent."""
    return ast.unparse(node) if node else None


def _args_to_params(*, arg_nodes: list[ast.arg]) -> list[Parameter]:
    """Convert a list of AST argument nodes to Parameter records."""
    return [
        Parameter(name=a.arg, annotation=_unparse_or_none(node=a.annotation))
        for a in arg_nodes
    ]


def _extract_params(*, args: ast.arguments) -> list[Parameter]:
    """Extract parameters from a function argument node, without defaults."""
    params: list[Parameter] = []

    params.extend(_args_to_params(arg_nodes=args.posonlyargs))
    if args.posonlyargs:
        params.append(Parameter(name="/"))

    params.extend(_args_to_params(arg_nodes=args.args))

    if args.vararg:
        params.append(
            Parameter(
                name=f"*{args.vararg.arg}",
                annotation=_unparse_or_none(node=args.vararg.annotation),
            )
        )
    elif args.kwonlyargs:
        params.append(Parameter(name="*"))

    params.extend(_args_to_params(arg_nodes=args.kwonlyargs))

    if args.kwarg:
        params.append(
            Parameter(
                name=f"**{args.kwarg.arg}",
                annotation=_unparse_or_none(node=args.kwarg.annotation),
            )
        )

    return params


def _extract_assignment(*, node: ast.Assign | ast.AnnAssign) -> AssignmentSymbol | None:
    """Build an AssignmentSymbol from an assignment or annotation.

    Returns None if the node's target is not a single simple name (e.g. tuple
    unpacking or attribute assignment), which is not a symbol.
    """
    if isinstance(node, ast.AnnAssign):
        if not isinstance(node.target, ast.Name):
            return None
        return AssignmentSymbol(
            name=node.target.id,
            annotation=ast.unparse(node.annotation),
            value=_unparse_or_none(node=node.value),
        )

    # ast.Assign
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    return AssignmentSymbol(name=node.targets[0].id, value=ast.unparse(node.value))


def _extract_function(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> FunctionSymbol:
    """Build a FunctionSymbol from a function or method AST node."""
    return FunctionSymbol(
        name=node.name,
        params=_extract_params(args=node.args),
        return_annotation=_unparse_or_none(node=node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _property_attribute(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> AssignmentSymbol:
    """Build an AssignmentSymbol representing a @property as a class attribute."""
    return AssignmentSymbol(
        name=node.name,
        annotation=_unparse_or_none(node=node.returns),
    )


def _extract_class(*, node: ast.ClassDef) -> ClassSymbol:
    """Build a ClassSymbol from a class AST node."""
    bases = [ast.unparse(b) for b in node.bases]

    attributes: list[AssignmentSymbol] = []
    methods: list[FunctionSymbol] = []

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.AnnAssign, ast.Assign)):
            assignment = _extract_assignment(node=child)
            if assignment is not None:
                attributes.append(assignment)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = property_kind(node=child)
            if kind in {"setter", "deleter"}:
                continue
            if kind == "property":
                attributes.append(_property_attribute(node=child))
            else:
                methods.append(_extract_function(node=child))

    return ClassSymbol(
        name=node.name,
        bases=bases,
        attributes=attributes,
        methods=methods,
    )


def extract_python_file(*, source: str, rel_path: str) -> PythonFile:
    """Parse Python source and extract its imports and its symbols."""
    tree = ast.parse(source)
    imports: list[str] = []
    symbols: list[Symbol] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.ClassDef):
            symbols.append(_extract_class(node=node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(_extract_function(node=node))
        elif isinstance(node, ast.TypeAlias):
            symbols.append(
                TypeAliasSymbol(name=node.name.id, value=ast.unparse(node.value))
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            assignment = _extract_assignment(node=node)
            if assignment is not None:
                symbols.append(assignment)

    return PythonFile(rel_path=rel_path, imports=imports, symbols=symbols)


def read_source_files(
    *, source_root: Path, project_directory: Path
) -> tuple[list[tuple[str, str]], list[SkippedFile]]:
    """Read every Python file under ``source_root``, keeping those that parse.

    Returns the ``(source_text, rel_path)`` pair of every readable, parseable
    file, and a :class:`SkippedFile` for every other one. Each ``rel_path`` is
    the file's path relative to ``project_directory``.

    Source files are read under their declared PEP 263 encoding, UTF-8
    default. A file is skipped when it fails to read (OSError,
    UnicodeDecodeError, or a SyntaxError from a malformed encoding cookie) or
    fails to parse (SyntaxError). Deciding this here lets
    ``extract_python_files`` trust that it only receives readable, parseable
    source.
    """
    source_root = source_root.resolve()
    project_directory = project_directory.resolve()

    files: list[tuple[str, str]] = []
    skipped: list[SkippedFile] = []
    for py_file in sorted(source_root.rglob("*.py")):
        rel_path = py_file.relative_to(project_directory).as_posix()
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


def extract_python_files(*, files: Iterable[tuple[str, str]]) -> list[PythonFile]:
    """Extract a :class:`PythonFile` for each file in *files* that has symbols.

    *files* holds the readable files from :func:`read_source_files`, as
    ``(source, rel_path)`` pairs where the source has already been
    confirmed parseable. Pure transformation: no IO, no warnings, no
    parsing decisions.
    """
    python_files = [
        extract_python_file(source=source, rel_path=rel_path)
        for source, rel_path in files
    ]
    return [python_file for python_file in python_files if python_file.symbols]
