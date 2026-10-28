"""Generate .pyi stub files for agent navigation."""

from collections.abc import Iterable
from pathlib import Path

from uncoded.extract import (
    AssignmentSymbol,
    ClassSymbol,
    FunctionSymbol,
    Parameter,
    PythonFile,
    TypeAliasSymbol,
    extract_python_file,
)
from uncoded.markers import GENERATED_MARKER
from uncoded.sync import remove_file, sync_file

# Width cap for inlining the right-hand side of an assignment. If the source of
# the right-hand side exceeds this, it is elided to "..." so stubs stay compact
# and stable.
VALUE_WIDTH_CAP = 80


def _render_value(*, value: str) -> str:
    """Return the source of a value, elided to '...' if too long or multi-line."""
    if len(value) > VALUE_WIDTH_CAP or "\n" in value:
        return "..."
    return value


def _render_param(*, param: Parameter) -> str:
    """Render a single parameter as a string for a function signature."""
    if param.name in ("/", "*"):
        return param.name
    if param.annotation:
        return f"{param.name}: {param.annotation}"
    return param.name


def _render_function(*, func: FunctionSymbol, indent: str = "") -> list[str]:
    """Render a function or method as stub lines, indented for methods."""
    params_str = ", ".join(_render_param(param=param) for param in func.params)
    ret = f" -> {func.return_annotation}" if func.return_annotation else ""
    prefix = "async def" if func.is_async else "def"
    lines = [f"{indent}{prefix} {func.name}({params_str}){ret}:"]
    lines.append(f"{indent}    ...")
    return lines


def _format_assignment(*, assignment: AssignmentSymbol | TypeAliasSymbol) -> str:
    """Render the 'name [: type] [= value]' portion of an assignment."""
    if isinstance(assignment, TypeAliasSymbol):
        return f"type {assignment.name} = {_render_value(value=assignment.value)}"
    head = (
        f"{assignment.name}: {assignment.annotation}"
        if assignment.annotation
        else assignment.name
    )
    if assignment.value is None:
        return head
    return f"{head} = {_render_value(value=assignment.value)}"


def _render_assignment(
    *, assignment: AssignmentSymbol | TypeAliasSymbol, indent: str = ""
) -> str:
    """Render an assignment, at module level or in a class body, as a stub line."""
    line = _format_assignment(assignment=assignment)
    return f"{indent}{line}"


def _render_class(*, cls: ClassSymbol) -> list[str]:
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


def render_stub(*, module: PythonFile) -> str:
    """Render a PythonFile as a .pyi file string."""
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
        module = extract_python_file(source=source, rel_path=rel_path)
        if not module.symbols:
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
