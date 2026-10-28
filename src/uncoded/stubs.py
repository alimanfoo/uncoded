"""Generate .pyi stub files for agent navigation."""

from pathlib import Path

from uncoded.extract import (
    AssignmentSymbol,
    ClassSymbol,
    FunctionSymbol,
    Parameter,
    PythonFile,
    TypeAliasSymbol,
)
from uncoded.markers import GENERATED_MARKER
from uncoded.sync import remove_file, sync_file

# Width cap for inlining the right-hand side of an assignment. If the source of
# the right-hand side exceeds this, it is elided to "..." so stubs stay compact
# and stable.
_VALUE_WIDTH_CAP = 80


def _render_value(*, value: str) -> str:
    """Return the source of a value, elided to '...' if too long or multi-line."""
    if len(value) > _VALUE_WIDTH_CAP or "\n" in value:
        return "..."
    return value


def _render_param(*, param: Parameter) -> str:
    """Render a single parameter as a string for a function signature."""
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


def _render_assignment(
    *, assignment: AssignmentSymbol | TypeAliasSymbol, indent: str = ""
) -> str:
    """Render an assignment, at module level or in a class body, as a stub line."""
    if isinstance(assignment, TypeAliasSymbol):
        value = _render_value(value=assignment.value)
        return f"{indent}type {assignment.name} = {value}"
    head = (
        f"{assignment.name}: {assignment.annotation}"
        if assignment.annotation
        else assignment.name
    )
    if assignment.value is None:
        return f"{indent}{head}"
    return f"{indent}{head} = {_render_value(value=assignment.value)}"


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


def _render_stub(*, python_file: PythonFile) -> str:
    """Render a PythonFile as a .pyi file string."""
    lines: list[str] = [f"# {GENERATED_MARKER}", f"# {python_file.rel_path}", ""]

    if python_file.imports:
        lines.extend(python_file.imports)
        lines.append("")

    lines.extend(
        _render_assignment(assignment=assignment)
        for assignment in python_file.assignments
    )
    if python_file.assignments:
        lines.append("")

    for func in python_file.functions:
        lines.extend(_render_function(func=func))
        lines.append("")

    for cls in python_file.classes:
        lines.extend(_render_class(cls=cls))

    return "\n".join(lines).rstrip() + "\n"


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
    python_files: list[PythonFile],
    output_dir: Path,
    project_directory: Path,
    check: bool,
) -> int:
    """Write the stub of each of ``python_files``, and remove every other stub.

    Every ``.pyi`` file under ``output_dir`` that ``python_files`` does not
    generate is removed, so ``python_files`` holds every file that keeps a stub.

    Each stub is written to ``project_directory / output_dir / <rel_path>``, with
    the ``.pyi`` suffix, where ``rel_path`` is the Python file's path relative to
    ``project_directory``.

    When ``check=True``, the on-disk tree is not mutated; instead,
    prospective writes and removals are reported and counted. Returns
    the number of changes (or prospective changes).
    """
    project_directory = project_directory.resolve()
    changes = 0
    expected: set[Path] = set()
    for python_file in python_files:
        stub_path = output_dir / Path(python_file.rel_path).with_suffix(".pyi")
        changes += sync_file(
            path=stub_path,
            content=_render_stub(python_file=python_file),
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
