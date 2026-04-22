"""Generate .pyi stub files for agent navigation."""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from uncoded.extract import _property_kind, iter_source_files
from uncoded.sync import remove_file, sync_file

# Width cap for inlining the right-hand side of an assignment. If the unparsed
# RHS exceeds this, it is elided to "..." and the reader follows the line range.
VALUE_WIDTH_CAP = 80


@dataclass
class StubParam:
    """A function parameter with name and optional type annotation."""

    name: str
    annotation: str | None = None


@dataclass
class StubFunction:
    """A function or method with its signature and line range."""

    name: str
    params: list[StubParam] = field(default_factory=list)
    return_annotation: str | None = None
    docstring_excerpt: str | None = None
    start_line: int = 0
    end_line: int = 0
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
    start_line: int = 0
    end_line: int = 0
    is_type_alias: bool = False


@dataclass
class StubClass:
    """A class with its members and line range."""

    name: str
    bases: list[str] = field(default_factory=list)
    docstring_excerpt: str | None = None
    start_line: int = 0
    end_line: int = 0
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


def _first_sentence(
    node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module,
) -> str | None:
    """Return the first sentence of a node's docstring, or None."""
    docstring = ast.get_docstring(node)
    if not docstring:
        return None
    text = docstring.strip()
    match = re.match(r"(.+?\.)\s", text + " ")
    if match:
        return match.group(1)
    return text.split("\n")[0].strip()


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


def _line_range(start: int, end: int) -> str:
    """Render a line range: 'L<start>' if single-line, else 'L<start>-<end>'."""
    return f"L{start}" if start == end else f"L{start}-{end}"


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
    start_line = node.lineno
    end_line = node.end_lineno or node.lineno

    if isinstance(node, ast.TypeAlias):
        if not isinstance(node.name, ast.Name):
            return None
        return StubAssignment(
            name=node.name.id,
            value_source=_render_value(node.value),
            start_line=start_line,
            end_line=end_line,
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
            start_line=start_line,
            end_line=end_line,
        )

    # ast.Assign
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        return None
    return StubAssignment(
        name=node.targets[0].id,
        value_source=_render_value(node.value),
        start_line=start_line,
        end_line=end_line,
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
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
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
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
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
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        attributes=attributes,
        methods=methods,
    )


def extract_stub(source: str, rel_path: str) -> StubModule:
    """Parse Python source and extract all symbols with signatures and line ranges."""
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
    lines = [
        f"{indent}{prefix} {func.name}({params_str}){ret}:  # {_line_range(func.start_line, func.end_line)}"  # noqa: E501
    ]
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
    """Render a module-level assignment as a stub line, with line range."""
    body = _format_assignment_body(a)
    return f"{indent}{body}  # {_line_range(a.start_line, a.end_line)}"


def _render_class_attribute(a: StubAssignment, indent: str = "    ") -> str:
    """Render a class attribute as a stub line (no line range — class has one)."""
    return f"{indent}{_format_assignment_body(a)}"


def render_stub(module: StubModule) -> str:
    """Render a StubModule as a .pyi file string."""
    lines: list[str] = [f"# {module.rel_path}", ""]

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
        range_str = _line_range(cls.start_line, cls.end_line)
        lines.append(f"class {cls.name}{bases_str}:  # {range_str}")
        if cls.docstring_excerpt:
            lines.append(f'    """{cls.docstring_excerpt}"""')
        lines.append("")

        for attr in cls.attributes:
            lines.append(_render_class_attribute(attr))
        if cls.attributes:
            lines.append("")

        for method in cls.methods:
            lines.extend(_render_function(method, indent="    "))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _generate_stubs(source_root: Path) -> dict[Path, str]:
    """Return a mapping from stub relative paths to rendered stub content."""
    result: dict[Path, str] = {}
    for source, rel_path in iter_source_files(source_root):
        try:
            module = extract_stub(source, rel_path)
        except SyntaxError:
            continue
        if not module.classes and not module.functions and not module.constants:
            continue
        result[Path(rel_path).with_suffix(".pyi")] = render_stub(module)
    return result


DEFAULT_STUBS_OUTPUT = Path(".uncoded/stubs")


def build_stubs(
    source_root: Path,
    output_dir: Path = DEFAULT_STUBS_OUTPUT,
    *,
    check: bool = False,
) -> int:
    """Sync stub files for all symbols under source_root, removing any orphans.

    Writes only files whose content has changed. After reconciling the current
    set of stubs, any pre-existing ``.pyi`` files in the corresponding subtree
    of ``output_dir`` whose source has been removed or renamed are deleted,
    and any directories left empty by the deletion are pruned. Only the
    subtree corresponding to ``source_root`` is touched, so other source
    roots' stubs are not affected.

    When ``check=True``, the on-disk tree is not mutated; instead, prospective
    writes and removals are reported and counted. Returns the number of
    changes (or prospective changes).
    """
    changes = 0
    expected: set[Path] = set()
    for rel_stub_path, content in _generate_stubs(source_root).items():
        stub_path = output_dir / rel_stub_path
        if sync_file(stub_path, content, check=check):
            changes += 1
        expected.add(stub_path.resolve())

    base = Path.cwd().resolve()
    try:
        source_rel = source_root.resolve().relative_to(base)
    except ValueError:
        # source_root is outside cwd; we have no safe subtree to clean.
        return changes
    stubs_root = output_dir / source_rel
    if not stubs_root.exists():
        return changes

    for existing in stubs_root.rglob("*.pyi"):
        if existing.resolve() not in expected and remove_file(existing, check=check):
            changes += 1

    if check:
        return changes

    # Prune now-empty directories, deepest-first, but keep stubs_root itself.
    for d in sorted(stubs_root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    return changes
