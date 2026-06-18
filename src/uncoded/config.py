"""Read uncoded configuration from pyproject.toml or .uncoded.toml."""

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


def _find_config_file(*, start: Path) -> Path | None:
    """Return the nearest config file walking up from ``start``.

    Checks each directory for ``pyproject.toml`` (tried first) then
    ``.uncoded.toml``. Skips any directory named ``.uncoded`` so generated
    artefacts are never mistaken for configuration. When the two files sit
    at different walk levels, the nearer one wins regardless of type;
    ``pyproject.toml`` only beats ``.uncoded.toml`` when both live in the
    same directory.
    """
    current = start.resolve()
    while True:
        if current.name != ".uncoded":
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                return pyproject
            uncoded_toml = current / ".uncoded.toml"
            if uncoded_toml.exists():
                return uncoded_toml
        parent = current.parent
        if parent == current:
            return None
        current = parent


def read_config(start: Path) -> Config | None:
    """Locate the config file and read all uncoded settings from it.

    Walks up from ``start`` looking for ``pyproject.toml`` or
    ``.uncoded.toml`` (see ``_find_config_file`` for precedence rules).
    Returns None when no config file is found. A found config file with
    no uncoded settings returns a Config with empty root lists — the
    caller is responsible for raising a "nothing to index" error when
    both root lists are empty.
    """
    config_file = _find_config_file(start=start)
    if config_file is None:
        return None

    with config_file.open("rb") as f:
        data = tomllib.load(f)

    if config_file.name == "pyproject.toml":
        try:
            section = data["tool"]["uncoded"]
        except KeyError:
            section = {}
    else:
        # .uncoded.toml uses top-level keys with no wrapper section.
        section = data

    source_roots = [Path(r) for r in section.get("source-roots", [])]
    doc_roots = [Path(r) for r in section.get("doc-roots", [])]

    raw_instruction_files = section.get("instruction-files")
    if raw_instruction_files is None:
        instruction_files = list(DEFAULT_INSTRUCTION_FILES)
    else:
        instruction_files = [Path(f) for f in raw_instruction_files]

    return Config(
        project_root=config_file.parent,
        source_roots=source_roots,
        doc_roots=doc_roots,
        instruction_files=instruction_files,
    )
