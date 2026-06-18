# src/uncoded/config.py

import tomllib
from dataclasses import dataclass
from pathlib import Path
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

def find_pyproject_toml(start: Path) -> Path | None:
    ...

def read_config(start: Path) -> Config | None:
    ...

class Config:
    project_root: Path
    source_roots: list[Path]
    doc_roots: list[Path]
    instruction_files: list[Path]
