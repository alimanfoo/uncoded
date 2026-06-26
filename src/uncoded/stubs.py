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
    """All symbols extracted from a single Python module."""

    rel_path: str
    imports: list[str] = field(default_factory=list)
    constants: list[StubAssignment] = field(default_factory=list)
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


def _extract_params(args: ast.arguments) -> list[StubParam]:
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


def _render_value(value: ast.expr) -> str:
    """Render an expression as source, eliding to '...' if too long or multi-line."""
    source = ast.unparse(value)
    if len(source) > VALUE_WIDTH_CAP or "\n" in source:
        return "..."
    return source


def _extract_assignment(
    node: ast.Assign | ast.AnnAssign | ast.TypeAlias,
) -> StubAssignment | None:
    """Build a StubAssignment from an assignment-style AST node.

    Returns None if the node's target is not a single simple name (e.g. tuple
    unpacking or attribute assignment), which we can't represent cleanly.
    """
    if isinstance(node, ast.TypeAlias):
        return StubAssignment(
            name=node.name.id,
            value_source=_render_value(node.value),
            is_pep695_alias=True,
        )

    if isinstance(node, ast.AnnAssign):
        if not isinstance(node.target, ast.Name):
            return None
        annotation = ast.unparse(node.annotation)
        value_source = _render_value(node.value) if node.value is not None else None
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
        value_source=_render_value(node.value),
    )


def _extract_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> StubFunction:
    """Build a StubFunction from a function or method AST node."""
    return StubFunction(
        name=node.name,
        params=_extract_params(node.args),
        return_annotation=_unparse_or_none(node=node.returns),
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _property_attribute(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> StubAssignment:
    """Build a StubAssignment representing a @property as a class attribute."""
    return StubAssignment(
        name=node.name,
        annotation=_unparse_or_none(node=node.returns),
    )


def _extract_class(node: ast.ClassDef) -> StubClass:
    """Build a StubClass from a class AST node."""
    bases = [ast.unparse(b) for b in node.bases]

    attributes: list[StubAssignment] = []
    methods: list[StubFunction] = []

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.AnnAssign, ast.Assign)):
            assignment = _extract_assignment(child)
            if assignment is not None:
                attributes.append(assignment)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = property_kind(child)
            if kind in {"setter", "deleter"}:
                continue
            if kind == "property":
                attributes.append(_property_attribute(child))
            else:
                methods.append(_extract_function(child))

    return StubClass(
        name=node.name,
        bases=bases,
        attributes=attributes,
        methods=methods,
    )


def extract_stub(source: str, rel_path: str) -> StubModule:
    """Parse Python source and extract imports, constants, classes, and functions."""
    tree = ast.parse(source)
    imports: list[str] = []
    constants: list[StubAssignment] = []
    classes: list[StubClass] = []
    functions: list[StubFunction] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.TypeAlias)):
            assignment = _extract_assignment(node)
            if assignment is not None:
                constants.append(assignment)

    return StubModule(
        rel_path=rel_path,
        imports=imports,
        constants=constants,
        classes=classes,
        functions=functions,
    )


def _render_param(p: StubParam) -> str:
    """Render a single parameter as a string for a function signature."""
    if p.name in ("/", "*"):
        return p.name
    if p.annotation:
        return f"{p.name}: {p.annotation}"
    return p.name


def _render_function(func: StubFunction, indent: str = "") -> list[str]:
    """Render a function or method as stub lines, indented for methods."""
    params_str = ", ".join(_render_param(p) for p in func.params)
    ret = f" -> {func.return_annotation}" if func.return_annotation else ""
    prefix = "async def" if func.is_async else "def"
    lines = [f"{indent}{prefix} {func.name}({params_str}){ret}:"]
    lines.append(f"{indent}    ...")
    return lines


def _format_assignment_body(a: StubAssignment) -> str:
    """Render the 'name [: type] [= value]' portion of an assignment."""
    if a.is_pep695_alias:
        return f"type {a.name} = {a.value_source}"
    head = f"{a.name}: {a.annotation}" if a.annotation else a.name
    if a.value_source is None:
        return head
    return f"{head} = {a.value_source}"


def _render_assignment(a: StubAssignment, indent: str = "") -> str:
    """Render a module-level assignment as a stub line."""
    body = _format_assignment_body(a)
    return f"{indent}{body}"


def _render_class(cls: StubClass) -> list[str]:
    bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
    lines = [f"class {cls.name}{bases_str}:"]
    if not cls.attributes and not cls.methods:
        lines.append("    ...")
        lines.append("")
        return lines
    lines.extend(_render_assignment(attr, indent="    ") for attr in cls.attributes)
    if cls.attributes:
        lines.append("")
    for method in cls.methods:
        lines.extend(_render_function(method, indent="    "))
        lines.append("")
    return lines


def render_stub(module: StubModule) -> str:
    """Render a StubModule as a .pyi file string."""
    lines: list[str] = [f"# {GENERATED_MARKER}", f"# {module.rel_path}", ""]

    if module.imports:
        lines.extend(module.imports)
        lines.append("")

    lines.extend(_render_assignment(const) for const in module.constants)
    if module.constants:
        lines.append("")

    for func in module.functions:
        lines.extend(_render_function(func))
        lines.append("")

    for cls in module.classes:
        lines.extend(_render_class(cls))

    return "\n".join(lines).rstrip() + "\n"


def _generate_stubs(files: Iterable[tuple[str, str]]) -> dict[Path, str]:
    """Return a mapping from stub relative paths to rendered stub content.

    *files* is the output of :func:`iter_source_files` — an iterable of
    ``(source, rel_path)`` pairs. Pure transformation: no IO, no
    warnings, no parsing decisions. Modules with no symbols are
    skipped.
    """
    result: dict[Path, str] = {}
    for source, rel_path in files:
        module = extract_stub(source, rel_path)
        if not module.classes and not module.functions and not module.constants:
            continue
        result[Path(rel_path).with_suffix(".pyi")] = render_stub(module)
    return result


def _resolve_stubs_root(
    *, source_root: Path, output_dir: Path, project_root: Path
) -> Path | None:
    # source_root must be under project_root; otherwise there is no safe subtree.
    try:
        source_rel = source_root.resolve().relative_to(project_root)
    except ValueError:
        return None
    abs_stubs_root = project_root / output_dir / source_rel
    return abs_stubs_root if abs_stubs_root.exists() else None


def _remove_orphan_stubs(
    *,
    expected: set[Path],
    abs_stubs_root: Path,
    project_root: Path,
    check: bool,
) -> int:
    changes = 0
    for existing in abs_stubs_root.rglob("*.pyi"):
        if existing.resolve() in expected:
            continue
        display = existing.relative_to(project_root)
        changes += remove_file(display, project_root=project_root, check=check)
    return changes


def _prune_empty_stub_dirs(*, abs_stubs_root: Path) -> None:
    # Prune now-empty directories, deepest-first, but keep abs_stubs_root itself.
    for d in sorted(
        abs_stubs_root.rglob("*"), key=lambda p: len(p.parts), reverse=True
    ):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def _write_stubs(
    *,
    stubs: dict[Path, str],
    source_root: Path,
    output_dir: Path,
    project_root: Path,
    check: bool,
) -> int:
    """Write each expected stub, remove orphans, and prune empty directories."""
    changes = 0
    expected: set[Path] = set()
    for rel_stub_path, content in stubs.items():
        stub_path = output_dir / rel_stub_path
        if sync_file(stub_path, content, project_root=project_root, check=check):
            changes += 1
        expected.add((project_root / stub_path).resolve())
    abs_stubs_root = _resolve_stubs_root(
        source_root=source_root, output_dir=output_dir, project_root=project_root
    )
    if abs_stubs_root is not None:
        changes += _remove_orphan_stubs(
            expected=expected,
            abs_stubs_root=abs_stubs_root,
            project_root=project_root,
            check=check,
        )
        if not check:
            _prune_empty_stub_dirs(abs_stubs_root=abs_stubs_root)
    return changes


def remove_all_stubs(output_dir: Path, *, project_root: Path, check: bool) -> int:
    """Remove all .pyi stubs under output_dir, then remove the root directory.

    Removes every .pyi file under ``output_dir``, reporting each as
    apply/check mode dictates, then (in apply mode) prunes now-empty
    directories deepest-first and removes the root itself. In check mode,
    reports prospective removals without touching disk. Returns the number
    of files removed (or that would be).
    """
    project_root = project_root.resolve()
    abs_output_dir = project_root / output_dir
    if not abs_output_dir.exists():
        return 0

    changes = 0
    for pyi_file in sorted(abs_output_dir.rglob("*.pyi")):
        display = pyi_file.relative_to(project_root)
        changes += remove_file(display, project_root=project_root, check=check)

    if check:
        return changes

    # Prune empty directories deepest-first. Skip any foreign file or non-empty
    # directory the tree should not contain.
    for d in sorted(
        abs_output_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True
    ):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    if not any(abs_output_dir.iterdir()):
        abs_output_dir.rmdir()

    return changes


def build_stubs(
    *,
    files: Iterable[tuple[str, str]],
    source_root: Path,
    output_dir: Path,
    project_root: Path,
    check: bool,
) -> int:
    """Sync stub files for all symbols under source_root, removing any orphans.

    The single stubs pipeline path: shared by ``cli._sync`` and the
    test suite so both callers run the same ``_generate_stubs`` →
    ``_write_stubs`` sequence. ``files`` is the materialised output of
    :func:`iter_source_files` — pre-iterated so callers that also need
    the files for other steps (the namespace map) do not walk source
    twice.

    ``project_root`` is the anchor for both ends of the pipeline:
    source paths in ``files`` are already relative to it (so each
    stub's rendered ``rel_path`` header matches :func:`iter_source_files`
    and the namespace map), and each stub is written to
    ``project_root / output_dir / <rel>``. The same ``project_root``
    must therefore be passed to :func:`iter_source_files` (for
    relativising) and to ``build_stubs`` (for writing); mismatched
    anchors silently produce wrong-looking stub paths.

    When ``check=True``, the on-disk tree is not mutated; instead,
    prospective writes and removals are reported and counted. Returns
    the number of changes (or prospective changes).
    """
    project_root = project_root.resolve()
    stubs = _generate_stubs(files)
    return _write_stubs(
        stubs=stubs,
        source_root=source_root,
        output_dir=output_dir,
        project_root=project_root,
        check=check,
    )
