"""Read project metadata and uncoded configuration from pyproject.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES


@dataclass(frozen=True)
class Config:
    """Uncoded configuration loaded from a project's config file."""

    project_root: Path
    source_roots: list[Path]
    doc_roots: list[Path]
    instruction_files: list[Path]


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


def read_config(start: Path) -> Config | None:
    """Locate pyproject.toml and read all uncoded settings from it.

    Walks up from ``start``. Returns None if no pyproject.toml is found.
    A found pyproject.toml with no ``[tool.uncoded]`` section returns a
    Config with empty root lists — the caller is responsible for raising
    a "nothing to index" error when both root lists are empty.
    """
    pyproject_path = find_pyproject_toml(start)
    if pyproject_path is None:
        return None

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        section = data["tool"]["uncoded"]
    except KeyError:
        section = {}

    source_roots = [Path(r) for r in section.get("source-roots", [])]
    doc_roots = [Path(r) for r in section.get("doc-roots", [])]

    raw_instruction_files = section.get("instruction-files")
    if raw_instruction_files is None:
        instruction_files = list(DEFAULT_INSTRUCTION_FILES)
    else:
        instruction_files = [Path(f) for f in raw_instruction_files]

    return Config(
        project_root=pyproject_path.parent,
        source_roots=source_roots,
        doc_roots=doc_roots,
        instruction_files=instruction_files,
    )
