"""Generate .pyi stub files for agent navigation."""

import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.ast_helpers import property_kind
from uncoded.markers import GENERATED_MARKER
from uncoded.sync import remove_file, sync_file

# Width cap for inlining the right-hand side of an assignment. If the unparsed
# RHS exceeds this, it is elided to "..." so stubs stay compact and stable.
VALUE_WIDTH_CAP = 80


@dataclass
class StubParam:
    """A function parameter with name and optional type annotation."""

    name: str
    annotation: str | None = None


@dataclass
class StubFunction:
    """A function or method with its signature."""

    name: str
    params: list[StubParam] = field(default_factory=list)
    return_annotation: str | None = None
    is_async: bool = False


@dataclass
class StubAssignment:
    """A module-level or class-level assignment.

    ``value_source`` is the rendered RHS if it fits within ``VALUE_WIDTH_CAP``,
    or the literal string ``"..."`` if the RHS was elided. ``None`` means there
    is no RHS at all (e.g. a bare annotation ``X: int``).
    """

    name: str
    annotation: str | None = None
    value_source: str | None = None
    is_pep695_alias: bool = False


@dataclass
class StubClass:
    """A class with its members."""

    name: str
    bases: list[str] = field(default_factory=list)
    attributes: list[StubAssignment] = field(default_factory=list)
    methods: list[StubFunction] = field(default_factory=list)


@dataclass
class StubModule:
    """What a stub holds for one Python file: its imports and its symbols."""

    rel_path: str
    imports: list[str] = field(default_factory=list)
    assignments: list[StubAssignment] = field(default_factory=list)
    classes: list[StubClass] = field(default_factory=list)
    functions: list[StubFunction] = field(default_factory=list)


def _unparse_or_none(*, node: ast.expr | None) -> str | None:
    """Unparse an optional annotation node, returning None when absent."""
    return ast.unparse(node) if node else None


def _args_to_params(*, arg_nodes: list[ast.arg]) -> list[StubParam]:
    """Convert a list of AST argument nodes to StubParam records."""
    return [
        StubParam(name=a.arg, annotation=_unparse_or_none(node=a.annotation))
        for a in arg_nodes
    ]


def _extract_params(*, args: ast.arguments) -> list[StubParam]:
    """Extract parameters from a function argument node, without defaults."""
    params: list[StubParam] = []

    params.extend(_args_to_params(arg_nodes=args.posonlyargs))
    if args.posonlyargs:
        params.append(StubParam(name="/"))

    params.extend(_args_to_params(arg_nodes=args.args))

    if args.vararg:
        params.append(
            StubParam(
                name=f"*{args.vararg.arg}",
                annotation=_unparse_or_none(node=args.vararg.annotation),
            )
        )
    elif args.kwonlyargs:
        params.append(StubParam(name="*"))

    params.extend(_args_to_params(arg_nodes=args.kwonlyargs))

    if args.kwarg:
        params.append(
            StubParam(
                name=f"**{args.kwarg.arg}",
                annotation=_unparse_or_none(node=args.kwarg.annotation),
            )
        )

    return params


def _render_value(*, value: ast.expr) -> str:
    """Render an expression as source, eliding to '...' if too long or multi-line."""
    source = ast.unparse(value)
    if len(source) > VALUE_WIDTH_CAP or "\n" in source:
        return "..."
    return source


def _extract_assignment(
    *,
    node: ast.Assign | ast.AnnAssign | ast.TypeAlias,
) -> StubAssignment | None:
    """Build a StubAssignment from an assignment-style AST node.

    Returns None if the node's target is not a single simple name (e.g. tuple
    unpacking or attribute assignment), which we can't represent cleanly.
    """
    if isinstance(node, ast.TypeAlias):
        return StubAssignment(
            name=node.name.id,
            value_source=_render_value(value=node.value),
            is_pep695_alias=True,
        )

    if isinstance(node, ast.AnnAssign):
        if not isinstance(node.target, ast.Name):
            return None
        annotation = ast.unparse(node.annotation)
        value_source = (
            _render_value(value=node.value) if node.value is not None else None
        )
        return StubAssignment(
            name=node.target.id,
            annotation=annotation,
            value_source=value_source,
        )

    # ast.Assign
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    return StubAssignment(
        name=node.targets[0].id,
        value_source=_render_value(value=node.value),
    )


def _extract_function(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> StubFunction:
    """Build a StubFunction from a function or method AST node."""
    return StubFunction(
        name=node.name,
        params=_extract_params(args=node.args),
        return_annotation=_unparse_or_none(node=node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _property_attribute(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> StubAssignment:
    """Build a StubAssignment representing a @property as a class attribute."""
    return StubAssignment(
        name=node.name,
        annotation=_unparse_or_none(node=node.returns),
    )


def _extract_class(*, node: ast.ClassDef) -> StubClass:
    """Build a StubClass from a class AST node."""
    bases = [ast.unparse(b) for b in node.bases]

    attributes: list[StubAssignment] = []
    methods: list[StubFunction] = []

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

    return StubClass(
        name=node.name,
        bases=bases,
        attributes=attributes,
        methods=methods,
    )


def extract_stub(*, source: str, rel_path: str) -> StubModule:
    """Parse Python source and extract imports, assignments, classes, and functions."""
    tree = ast.parse(source)
    imports: list[str] = []
    assignments: list[StubAssignment] = []
    classes: list[StubClass] = []
    functions: list[StubFunction] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node=node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node=node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.TypeAlias)):
            assignment = _extract_assignment(node=node)
            if assignment is not None:
                assignments.append(assignment)

    return StubModule(
        rel_path=rel_path,
        imports=imports,
        assignments=assignments,
        classes=classes,
        functions=functions,
    )


def _render_param(*, param: StubParam) -> str:
    """Render a single parameter as a string for a function signature."""
    if param.name in ("/", "*"):
        return param.name
    if param.annotation:
        return f"{param.name}: {param.annotation}"
    return param.name


def _render_function(*, func: StubFunction, indent: str = "") -> list[str]:
    """Render a function or method as stub lines, indented for methods."""
    params_str = ", ".join(_render_param(param=param) for param in func.params)
    ret = f" -> {func.return_annotation}" if func.return_annotation else ""
    prefix = "async def" if func.is_async else "def"
    lines = [f"{indent}{prefix} {func.name}({params_str}){ret}:"]
    lines.append(f"{indent}    ...")
    return lines


def _format_assignment(*, assignment: StubAssignment) -> str:
    """Render the 'name [: type] [= value]' portion of an assignment."""
    if assignment.is_pep695_alias:
        return f"type {assignment.name} = {assignment.value_source}"
    head = (
        f"{assignment.name}: {assignment.annotation}"
        if assignment.annotation
        else assignment.name
    )
    if assignment.value_source is None:
        return head
    return f"{head} = {assignment.value_source}"


def _render_assignment(*, assignment: StubAssignment, indent: str = "") -> str:
    """Render an assignment, at module level or in a class body, as a stub line."""
    line = _format_assignment(assignment=assignment)
    return f"{indent}{line}"


def _render_class(*, cls: StubClass) -> list[str]:
    bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
    lines = [f"class {cls.name}{bases_str}:"]
    if not cls.attributes and not cls.methods:
        lines.append("    ...")
        lines.append("")
        return lines
    lines.extend(
        _render_assignment(assignment=attr, indent="    ") for attr in cls.attributes
    )
    if cls.attributes:
        lines.append("")
    for method in cls.methods:
        lines.extend(_render_function(func=method, indent="    "))
        lines.append("")
    return lines


def render_stub(*, module: StubModule) -> str:
    """Render a StubModule as a .pyi file string."""
    lines: list[str] = [f"# {GENERATED_MARKER}", f"# {module.rel_path}", ""]

    if module.imports:
        lines.extend(module.imports)
        lines.append("")

    lines.extend(
        _render_assignment(assignment=assignment) for assignment in module.assignments
    )
    if module.assignments:
        lines.append("")

    for func in module.functions:
        lines.extend(_render_function(func=func))
        lines.append("")

    for cls in module.classes:
        lines.extend(_render_class(cls=cls))

    return "\n".join(lines).rstrip() + "\n"


def _generate_stubs(*, files: Iterable[tuple[str, str]]) -> dict[Path, str]:
    """Return a mapping from stub relative paths to rendered stub content.

    *files* holds the readable files from :func:`read_source_files`, as
    ``(source, rel_path)`` pairs. Pure transformation: no IO, no
    warnings, no parsing decisions. Modules with no symbols are
    skipped.
    """
    result: dict[Path, str] = {}
    for source, rel_path in files:
        module = extract_stub(source=source, rel_path=rel_path)
        if not module.classes and not module.functions and not module.assignments:
            continue
        result[Path(rel_path).with_suffix(".pyi")] = render_stub(module=module)
    return result


def _remove_orphan_stubs(
    *,
    expected: set[Path],
    stubs_dir: Path,
    project_directory: Path,
    check: bool,
) -> int:
    changes = 0
    # The walk finishes before the first removal, because remove_file also
    # removes the directories that it leaves empty.
    for existing in sorted(stubs_dir.rglob("*.pyi")):
        if existing.resolve() in expected:
            continue
        display = existing.relative_to(project_directory)
        changes += remove_file(
            path=display, project_directory=project_directory, check=check
        )
    return changes


def sync_stubs(
    *,
    files: Iterable[tuple[str, str]],
    output_dir: Path,
    project_directory: Path,
    check: bool,
) -> int:
    """Write the stub of each file in ``files``, and remove every other stub.

    ``files`` holds ``(source, rel_path)`` pairs from :func:`read_source_files`.
    Every ``.pyi`` file under ``output_dir`` that ``files`` does not generate is
    removed, so ``files`` holds every file that keeps a stub.

    ``project_directory`` is the anchor for both ends of the pipeline:
    source paths in ``files`` are already relative to it (so each
    stub's rendered ``rel_path`` header matches :func:`read_source_files`
    and the namespace map), and each stub is written to
    ``project_directory / output_dir / <rel>``. The same ``project_directory``
    must therefore be passed to :func:`read_source_files` (for
    relativising) and to ``sync_stubs`` (for writing); mismatched
    anchors silently produce wrong-looking stub paths.

    When ``check=True``, the on-disk tree is not mutated; instead,
    prospective writes and removals are reported and counted. Returns
    the number of changes (or prospective changes).
    """
    project_directory = project_directory.resolve()
    changes = 0
    expected: set[Path] = set()
    for rel_stub_path, content in _generate_stubs(files=files).items():
        stub_path = output_dir / rel_stub_path
        changes += sync_file(
            path=stub_path,
            content=content,
            project_directory=project_directory,
            check=check,
        )
        expected.add((project_directory / stub_path).resolve())
    changes += _remove_orphan_stubs(
        expected=expected,
        stubs_dir=project_directory / output_dir,
        project_directory=project_directory,
        check=check,
    )
    return changes
