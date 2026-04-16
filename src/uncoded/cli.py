"""CLI entry point for uncoded."""

import sys
from pathlib import Path

from uncoded.claude_md import sync_claude_md
from uncoded.config import read_source_roots
from uncoded.extract import walk_source
from uncoded.namespace_map import build_map, render_map
from uncoded.stubs import DEFAULT_STUBS_OUTPUT, build_stubs

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def main() -> int:
    """Build the namespace map, stub files, and CLAUDE.md navigation section."""
    try:
        source_roots = [r.resolve() for r in read_source_roots()]
    except (FileNotFoundError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for root in source_roots:
        if not root.is_dir():
            print(f"Error: {root} is not a directory", file=sys.stderr)
            return 1

    modules = [m for root in source_roots for m in walk_source(root)]
    map_content = render_map(build_map(modules))
    DEFAULT_MAP_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_MAP_OUTPUT.write_text(map_content)
    print(f"Wrote {DEFAULT_MAP_OUTPUT}")

    for root in source_roots:
        build_stubs(root)

    sync_claude_md()
    return 0
