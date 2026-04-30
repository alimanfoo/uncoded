# src/uncoded/config.py

import tomllib
from pathlib import Path
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

def find_pyproject_toml() -> Path | None:
    """Search for pyproject.toml starting from cwd, walking up."""
    ...

def read_project_name() -> str:
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def read_source_roots() -> list[Path]:
    """Read source roots from [tool.uncoded] source-roots in pyproject.toml."""
    ...

def read_instruction_files() -> list[Path]:
    """Read instruction files from [tool.uncoded] instruction-files in pyproject.toml."""
    ...
