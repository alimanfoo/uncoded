# src/uncoded/cli.py

import sys
from pathlib import Path
from uncoded.claude_md import sync_claude_md
from uncoded.config import read_source_roots
from uncoded.extract import walk_source
from uncoded.namespace_map import build_map, render_map
from uncoded.stubs import DEFAULT_STUBS_OUTPUT, build_stubs

def main() -> int:  # L15-38
    """Build the namespace map, stub files, and CLAUDE.md navigation section."""
    ...
