"""Generate .pyi stub files for agent navigation."""

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.extract import _property_kind, iter_source_files
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
    docstring_excerpt: str | None = None
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
    is_type_alias: bool = False


@dataclass
class StubClass:
    """A class with its members."""

    name: str
    bases: list[str] = field(default_factory=list)
    docstring_excerpt: str | None = None
    attributes: list[StubAssignment] = field(default_factory=list)
    methods: list[StubFunction] = field(default_factory=list)


@dataclass
class StubModule:
    """All symbols extracted from a single Python module."""

    rel_path: str
    docstring_excerpt: str | None = None
    imports: list[str] = field(default_factory=list)
    constants: list[StubAssignment] = field(default_factory=list)
    classes: list[StubClass] = field(default_factory=list)
    functions: list[StubFunction] = field(default_factory=list)


def _first_sentence(
    node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module,
) -> str | None:
    """Return the first sentence, or first line, of a node's docstring.

    The contract is "first sentence or first line, whichever comes
    first," so the consumer (the stub renderer) always receives a
    single-line excerpt suitable for a one-line ``.pyi`` docstring.

    A sentence boundary is a period followed by whitespace and a
    capital letter. The capital-letter requirement deliberately
    avoids truncation at lowercase-after-period abbreviations like
    ``e.g.``, ``i.e.``, and ``U.S.``. When no such boundary exists
    in the docstring, the function falls back to the substring up
    to the first newline, so single-line docstrings without a
    trailing period and multi-line docstrings without an internal
    sentence boundary still yield a usable excerpt.

    Returns ``None`` only when the node has no docstring or the
    docstring is whitespace-only. (``ast.get_docstring(clean=True)``
    normalises whitespace-only docstrings to ``""``.)

    Documented non-contract: docstrings starting with capital-letter
    abbreviations such as ``Mr. Smith arrived.`` or ``Dr. Jones``
    truncate at the abbreviation. The heuristic cannot tell a
    title-plus-name from a true sentence break; disambiguating these
    would require a tokeniser or a whitelist, which the function
    deliberately stops short of.
    """
    docstring = ast.get_docstring(node)
    if not docstring:
        return None
    match = re.match(r"(.+?\.(?=\s+[A-Z])|.+?(?=\n))", docstring.strip() + "\n")
    # docstring is non-empty post-cleandoc, so .strip() leaves at least
    # one non-whitespace character; alt-2 ``.+?(?=\n)`` always matches.
    assert match is not None
    return match.group(1)


def _extract_params(args: ast.arguments) -> list[StubParam]:
    """Extract parameters from a function argument node, without defaults."""
    params: list[StubParam] = []

    for arg in args.posonlyargs:
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        params.append(StubParam(name=arg.arg, annotation=annotation))
    if args.posonlyargs:
        params.append(StubParam(name="/"))

    for arg in args.args:
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        params.append(StubParam(name=arg.arg, annotation=annotation))

    if args.vararg:
        annotation = (
            ast.unparse(args.vararg.annotation) if args.vararg.annotation else None
        )
        params.append(StubParam(name=f"*{args.vararg.arg}", annotation=annotation))
    elif args.kwonlyargs:
        params.append(StubParam(name="*"))

    for arg in args.kwonlyargs:
        annotation = ast.unparse(arg.annotation) if arg.annotation else None
        params.append(StubParam(name=arg.arg, annotation=annotation))

    if args.kwarg:
        annotation = (
            ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None
        )
        params.append(StubParam(name=f"**{args.kwarg.arg}", annotation=annotation))

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
        if not isinstance(node.name, ast.Name):
            return None
        return StubAssignment(
            name=node.name.id,
            value_source=_render_value(node.value),
            is_type_alias=True,
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
        return_annotation=ast.unparse(node.returns) if node.returns else None,
        docstring_excerpt=_first_sentence(node),
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _property_attribute(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> StubAssignment:
    """Build a StubAssignment representing a @property as a class attribute."""
    return StubAssignment(
        name=node.name,
        annotation=ast.unparse(node.returns) if node.returns else None,
        value_source=None,
        is_type_alias=False,
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
            kind = _property_kind(child)
            if kind == "setter" or kind == "deleter":
                continue
            if kind == "property":
                attributes.append(_property_attribute(child))
            else:
                methods.append(_extract_function(child))

    return StubClass(
        name=node.name,
        bases=bases,
        docstring_excerpt=_first_sentence(node),
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
        docstring_excerpt=_first_sentence(tree),
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
    if func.docstring_excerpt:
        lines.append(f'{indent}    """{func.docstring_excerpt}"""')
    lines.append(f"{indent}    ...")
    return lines


def _format_assignment_body(a: StubAssignment) -> str:
    """Render the 'name [: type] [= value]' portion of an assignment."""
    if a.is_type_alias:
        return f"type {a.name} = {a.value_source}"
    head = f"{a.name}: {a.annotation}" if a.annotation else a.name
    if a.value_source is None:
        return head
    return f"{head} = {a.value_source}"


def _render_assignment(a: StubAssignment, indent: str = "") -> str:
    """Render a module-level assignment as a stub line."""
    body = _format_assignment_body(a)
    return f"{indent}{body}"


def render_stub(module: StubModule) -> str:
    """Render a StubModule as a .pyi file string."""
    lines: list[str] = [f"# {module.rel_path}", ""]

    if module.docstring_excerpt:
        lines.append(f'"""{module.docstring_excerpt}"""')
        lines.append("")

    if module.imports:
        lines.extend(module.imports)
        lines.append("")

    for const in module.constants:
        lines.append(_render_assignment(const))
    if module.constants:
        lines.append("")

    for func in module.functions:
        lines.extend(_render_function(func))
        lines.append("")

    for cls in module.classes:
        bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
        lines.append(f"class {cls.name}{bases_str}:")
        if cls.docstring_excerpt:
            lines.append(f'    """{cls.docstring_excerpt}"""')
        lines.append("")

        for attr in cls.attributes:
            lines.append(_render_assignment(attr, indent="    "))
        if cls.attributes:
            lines.append("")

        for method in cls.methods:
            lines.extend(_render_function(method, indent="    "))
            lines.append("")

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


DEFAULT_STUBS_OUTPUT = Path(".uncoded/stubs")


def _write_stubs(
    *,
    stubs: dict[Path, str],
    source_root: Path,
    output_dir: Path,
    project_root: Path | None,
    check: bool,
) -> int:
    """Write *stubs* under *output_dir* and prune orphans under *source_root*.

    *stubs* maps each stub's relative path (under *output_dir*) to its
    rendered content; typically the return value of
    :func:`_generate_stubs`.

    ``project_root`` is the single project anchor. When provided, it
    must already be resolved; ``output_dir`` is treated as relative to
    it for filesystem I/O while printed messages remain
    project-relative, and the orphan-cleanup subtree is anchored at
    ``output_dir / source_root.relative_to(project_root)`` (so
    ``project_root`` must be an ancestor of ``source_root`` for cleanup
    to run; otherwise cleanup is skipped). When ``None``, paths resolve
    against the current working directory and the cleanup anchor uses
    ``Path.cwd()`` in place of ``project_root``.

    Writes only files whose content has changed. After reconciling the
    current set of stubs, any pre-existing ``.pyi`` files in the
    corresponding subtree whose source has been removed or renamed are
    deleted, and any directories left empty by the deletion are
    pruned. Only the subtree corresponding to ``source_root`` is
    touched, so other source roots' stubs are not affected.

    When ``check=True``, the on-disk tree is not mutated; instead,
    prospective writes and removals are reported and counted. Returns
    the number of changes (or prospective changes).
    """
    anchor = project_root if project_root is not None else Path.cwd()
    changes = 0
    expected: set[Path] = set()
    for rel_stub_path, content in stubs.items():
        stub_path = output_dir / rel_stub_path
        if sync_file(stub_path, content, root=project_root, check=check):
            changes += 1
        anchored = project_root / stub_path if project_root is not None else stub_path
        expected.add(anchored.resolve())

    try:
        source_rel = source_root.resolve().relative_to(anchor)
    except ValueError:
        # source_root is outside the anchor; no safe subtree to clean.
        return changes
    stubs_root = output_dir / source_rel
    abs_stubs_root = (
        project_root / stubs_root if project_root is not None else stubs_root
    )
    if not abs_stubs_root.exists():
        return changes

    for existing in abs_stubs_root.rglob("*.pyi"):
        if existing.resolve() in expected:
            continue
        display = (
            existing.relative_to(project_root) if project_root is not None else existing
        )
        if remove_file(display, root=project_root, check=check):
            changes += 1

    if check:
        return changes

    # Prune now-empty directories, deepest-first, but keep abs_stubs_root itself.
    for d in sorted(
        abs_stubs_root.rglob("*"), key=lambda p: len(p.parts), reverse=True
    ):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    return changes


def _build_stubs(
    *,
    source_root: Path,
    output_dir: Path,
    project_root: Path,
    check: bool,
) -> int:
    """Sync stub files for all symbols under source_root, removing any orphans.

    Internal end-to-end helper used by the test suite. Stub paths are
    rendered relative to *project_root*, so the rendered ``rel_path``
    headers match the project-relative paths that :func:`walk_source`
    and the namespace map use.

    When ``check=True``, the on-disk tree is not mutated; instead,
    prospective writes and removals are reported and counted. Returns
    the number of changes (or prospective changes).
    """
    project_root = project_root.resolve()
    stubs = _generate_stubs(iter_source_files(source_root, project_root))
    return _write_stubs(
        stubs=stubs,
        source_root=source_root,
        output_dir=output_dir,
        project_root=project_root,
        check=check,
    )
