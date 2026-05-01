# src/uncoded/cli.py

"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path
from uncoded.config import read_instruction_files, read_source_roots
from uncoded.extract import walk_source
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.serena_setup import setup
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs
from uncoded.sync import sync_file

DEFAULT_MAP_OUTPUT = Path('.uncoded/namespace.yaml')

def _sync(*, check: bool) -> int:
    """Sync (or verify) the namespace map, stub files, and instruction-file sections."""
    ...

def main() -> int:
    """Dispatch the uncoded CLI."""
    ...
