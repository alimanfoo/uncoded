# src/uncoded/config.py

"""Read project metadata and uncoded configuration from pyproject.toml."""

import tomllib
from pathlib import Path
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

def find_pyproject_toml(start: Path) -> Path | None:
    """Walk up from ``start`` looking for ``pyproject.toml``."""
    ...

def read_project_name(start: Path) -> str:
    """Read the project name, falling back to the start-dir name."""
    ...

def read_source_roots(pyproject_path: Path) -> list[Path]:
    """Read source roots from ``[tool.uncoded] source-roots``."""
    ...

def read_instruction_files(start: Path) -> list[Path]:
    """Read ``[tool.uncoded] instruction-files`` from ``pyproject.toml``."""
    ...
