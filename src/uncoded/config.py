"""Read project metadata and uncoded configuration from pyproject.toml."""

import tomllib
from pathlib import Path

from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES


def find_pyproject_toml(start: Path) -> Path | None:
    """Walk up from ``start`` looking for ``pyproject.toml``."""
    current = start.resolve()
    while True:
        candidate = current / "pyproject.toml"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def read_project_name(start: Path) -> str:
    """Read the project name, falling back to the start-dir name.

    ``start`` is the directory the upward walk for ``pyproject.toml``
    begins from, and is also the source of the fallback name when no
    ``pyproject.toml`` is found or its ``[project]`` table lacks a
    ``name``. Threading ``start`` through both halves keeps the project
    name aligned with the directory the caller is configuring; every
    caller spells the directory explicitly so an implicit-cwd default
    cannot drift the two halves apart.
    """
    base = start.resolve()
    toml_path = find_pyproject_toml(base)
    if toml_path is None:
        return base.name
    with toml_path.open("rb") as f:
        data = tomllib.load(f)
    try:
        return data["project"]["name"]
    except KeyError:
        return base.name


def read_source_roots(pyproject_path: Path) -> list[Path]:
    """Read source roots from ``[tool.uncoded] source-roots``.

    Reads the section from the given ``pyproject.toml`` (which the
    caller must guarantee exists). Raises :class:`LookupError` if the
    section is missing. Returns the configured paths as a list of
    :class:`Path` instances on success.
    """
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        roots = data["tool"]["uncoded"]["source-roots"]
    except KeyError:
        raise LookupError(
            "No [tool.uncoded] source-roots found in pyproject.toml. "
            "Add [tool.uncoded] source-roots to configure."
        ) from None

    return [Path(r) for r in roots]


def read_instruction_files(start: Path) -> list[Path]:
    """Read ``[tool.uncoded] instruction-files`` from ``pyproject.toml``.

    ``start`` is the directory the upward walk begins from. Falls back
    to ``DEFAULT_INSTRUCTION_FILES`` if the key is absent or no
    ``pyproject.toml`` is found, so that ``uncoded`` works on a fresh
    repo without explicit configuration.
    """
    toml_path = find_pyproject_toml(start)
    if toml_path is None:
        return list(DEFAULT_INSTRUCTION_FILES)

    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        files = data["tool"]["uncoded"]["instruction-files"]
    except KeyError:
        return list(DEFAULT_INSTRUCTION_FILES)

    return [Path(f) for f in files]
