"""Extract symbols from Python source files using the AST."""

import ast
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.ast_helpers import (
    MemberNode,
    SymbolNode,
    class_symbols,
    module_symbols,
    property_kind,
)
from uncoded.read_helpers import (
    SkippedFile,
    failure_reason,
    read_source_text,
    root_files,
)


@dataclass
class Parameter:
    """A function parameter with its name and any annotation.

    ``/`` stands for the separator after positional-only parameters, and ``*``
    for the separator before keyword-only parameters.
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
    """An assignment or annotation whose one target is a bare name.

    ``value`` is the source of the right-hand side, or None when there is none,
    as for a bare annotation ``X: int``.
    """

    name: str
    annotation: str | None = None
    value: str | None = None


@dataclass(frozen=True)
class PropertySymbol:
    """A property with its name and any return annotation."""

    name: str
    annotation: str | None = None


@dataclass
class TypeAliasSymbol:
    """A ``type`` statement, with the source of its value."""

    name: str
    value: str


@dataclass
class ClassSymbol:
    """A class with its bases and every definition in its class body.

    ``members`` keeps source order and every definition of a redefined name.
    """

    name: str
    bases: list[str] = field(default_factory=list)
    members: list[AssignmentSymbol | FunctionSymbol | PropertySymbol] = field(
        default_factory=list
    )


type Symbol = AssignmentSymbol | TypeAliasSymbol | ClassSymbol | FunctionSymbol


@dataclass
class PythonFile:
    """A Python file's imports and every definition in its module body.

    ``symbols`` keeps source order and every definition of a redefined name.
    """

    rel_path: str
    imports: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)


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


def _extract_assignment(
    *, name: str, node: ast.Assign | ast.AnnAssign
) -> AssignmentSymbol:
    """Build the AssignmentSymbol that ``node`` defines as ``name``."""
    if isinstance(node, ast.AnnAssign):
        return AssignmentSymbol(
            name=name,
            annotation=ast.unparse(node.annotation),
            value=_unparse_or_none(node=node.value),
        )
    return AssignmentSymbol(name=name, value=ast.unparse(node.value))


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


def _extract_property(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> PropertySymbol:
    """Build a PropertySymbol from a @property getter."""
    return PropertySymbol(
        name=node.name,
        annotation=_unparse_or_none(node=node.returns),
    )


def _extract_member(
    *, name: str, node: MemberNode
) -> AssignmentSymbol | FunctionSymbol | PropertySymbol:
    """Build the member that ``node`` defines as ``name`` in a class body."""
    if isinstance(node, (ast.AnnAssign, ast.Assign)):
        return _extract_assignment(name=name, node=node)
    if property_kind(node=node) == "property":
        return _extract_property(node=node)
    return _extract_function(node=node)


def _extract_class(*, node: ast.ClassDef) -> ClassSymbol:
    """Build a ClassSymbol from a class AST node."""
    return ClassSymbol(
        name=node.name,
        bases=[ast.unparse(b) for b in node.bases],
        members=[
            _extract_member(name=name, node=child)
            for name, child in class_symbols(node=node)
        ],
    )


def _extract_symbol(*, name: str, node: SymbolNode) -> Symbol:
    """Build the symbol that ``node`` defines as ``name`` in a module body."""
    if isinstance(node, ast.ClassDef):
        return _extract_class(node=node)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _extract_function(node=node)
    if isinstance(node, ast.TypeAlias):
        return TypeAliasSymbol(name=name, value=ast.unparse(node.value))
    return _extract_assignment(name=name, node=node)


def _extract_python_file(*, source: str, rel_path: str) -> PythonFile:
    """Parse Python source and extract its imports and its symbols."""
    tree = ast.parse(source)
    return PythonFile(
        rel_path=rel_path,
        imports=[
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ],
        symbols=[
            _extract_symbol(name=name, node=node)
            for name, node in module_symbols(tree=tree)
        ],
    )


def read_python_files(
    *, source_roots: list[Path], project_directory: Path
) -> tuple[list[PythonFile], list[SkippedFile]]:
    """Read every Python file under ``source_roots`` that has symbols.

    Returns the :class:`PythonFile` of every readable, parseable file that has
    symbols, and a :class:`SkippedFile` for every file that cannot be read or
    parsed. Each ``rel_path`` is the file's path relative to
    ``project_directory``.

    Source files are read under their declared PEP 263 encoding, UTF-8
    default. A file is skipped when it fails to read (OSError,
    UnicodeDecodeError, or a SyntaxError from a malformed encoding cookie) or
    fails to parse (SyntaxError).
    """
    python_files: list[PythonFile] = []
    skipped: list[SkippedFile] = []
    for source_root in source_roots:
        for py_file, rel_path in root_files(
            root=source_root, pattern="*.py", project_directory=project_directory
        ):
            try:
                source = read_source_text(path=py_file)
            except (OSError, UnicodeDecodeError, SyntaxError) as e:
                skipped.append(
                    SkippedFile(path=rel_path, reason=failure_reason(error=e))
                )
                continue
            try:
                python_file = _extract_python_file(source=source, rel_path=rel_path)
            except SyntaxError as e:
                reason = f"SyntaxError at line {e.lineno}: {e.msg}"
                skipped.append(SkippedFile(path=rel_path, reason=reason))
                continue
            if python_file.symbols:
                python_files.append(python_file)
    return python_files, skipped
