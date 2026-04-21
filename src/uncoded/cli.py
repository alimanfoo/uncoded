"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.config import read_instruction_files, read_source_roots
from uncoded.extract import walk_source
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.serena_setup import setup_serena
from uncoded.stubs import build_stubs

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def _build() -> int:
    """Build the namespace map, stub files, and instruction-file navigation sections."""
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

    for path in read_instruction_files():
        sync_instruction_file(path)
    return 0


def main() -> int:
    """Dispatch the uncoded CLI.

    With no subcommand, rebuilds the navigation index (default behaviour).
    The ``setup-serena`` subcommand generates MCP and Claude Code config
    for the recommended Serena + ty LSP integration.
    """
    parser = argparse.ArgumentParser(
        prog="uncoded",
        description=(
            "Build a navigation index for AI coding agents. Run with no "
            "arguments to (re)build the index."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "setup-serena",
        help=(
            "Write .mcp.json, .serena/project.yml, and .claude/settings.json "
            "for the recommended Serena + ty LSP integration."
        ),
    )
    args = parser.parse_args()

    if args.command == "setup-serena":
        return setup_serena()
    return _build()
