# src/uncoded/cli.py

import argparse
import sys
from pathlib import Path
from uncoded.config import read_instruction_files, read_source_roots
from uncoded.extract import walk_source
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.serena_setup import setup_serena
from uncoded.stubs import build_stubs
from uncoded.sync import sync_file

DEFAULT_MAP_OUTPUT = Path('.uncoded/namespace.yaml')  # L15

def _sync(*, check: bool) -> int:  # L18-57
    """Sync (or verify) the namespace map, stub files, and instruction-file sections."""
    ...

def main() -> int:  # L60-99
    """Dispatch the uncoded CLI."""
    ...
