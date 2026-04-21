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

DEFAULT_MAP_OUTPUT = Path('.uncoded/namespace.yaml')  # L14

def _build() -> int:  # L17-41
    """Build the namespace map, stub files, and instruction-file navigation sections."""
    ...

def main() -> int:  # L44-70
    """Dispatch the uncoded CLI."""
    ...
