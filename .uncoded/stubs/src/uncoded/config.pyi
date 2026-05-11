# src/uncoded/config.py

import tomllib
from pathlib import Path
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

def find_pyproject_toml(start: Path) -> Path | None:
    ...

def read_project_name(start: Path) -> str:
    ...

def read_source_roots(pyproject_path: Path) -> list[Path]:
    ...

def read_instruction_files(start: Path) -> list[Path]:
    ...
