# src/uncoded/cli.py

import argparse
import sys
from pathlib import Path
from uncoded.body import SymbolNotFound, UnsupportedNamePath, resolve_body
from uncoded.config import find_pyproject_toml, read_instruction_files, read_source_roots
from uncoded.extract import extract_modules, iter_source_files
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.serena_setup import setup
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs
from uncoded.sync import sync_file

def _find_project_root(*, start: Path) -> Path | None:
    ...

def _sync(*, start: Path | None, check: bool) -> int:
    ...

def _body(*, name_path: str, in_path: str) -> int:
    ...

def _refs(*, name_path: str, in_path: str) -> int:
    ...

def main() -> int:
    ...
