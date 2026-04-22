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
from uncoded.sync import sync_file

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def _build(*, check: bool = False) -> int:
    """Build (or verify) the namespace map, stub files, and instruction-file sections.

    When ``check=True``, the on-disk tree is not mutated: each step reports
    whether it would write. Returns 1 if any step reports a prospective
    change (so CI can gate on a stale index), 0 if the tree is already in
    sync. In apply mode, returns 0 on success or 1 on configuration error.
    """
    try:
        source_roots = [r.resolve() for r in read_source_roots()]
    except (FileNotFoundError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for root in source_roots:
        if not root.is_dir():
            print(f"Error: {root} is not a directory", file=sys.stderr)
            return 1

    changes = 0

    modules = [m for root in source_roots for m in walk_source(root)]
    map_content = render_map(build_map(modules))
    if sync_file(DEFAULT_MAP_OUTPUT, map_content, check=check):
        changes += 1

    for root in source_roots:
        changes += build_stubs(root, check=check)

    for path in read_instruction_files():
        if sync_instruction_file(path, check=check):
            changes += 1

    if check:
        if changes:
            print(f"Index out of date: {changes} file(s) would change.")
            return 1
        print("Index is up to date.")
        return 0
    return 0


def main() -> int:
    """Dispatch the uncoded CLI.

    With no subcommand, rebuilds the navigation index (default behaviour);
    with ``--check``, reports whether a rebuild would change anything and
    exits non-zero if so. The ``setup-serena`` subcommand generates MCP and
    Claude Code config for the recommended Serena + ty LSP integration.
    """
    parser = argparse.ArgumentParser(
        prog="uncoded",
        description=(
            "Build a navigation index for AI coding agents. Run with no "
            "arguments to (re)build the index."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Verify the index is up to date without writing. Exits non-zero "
            "if any file would change. Useful in CI."
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
    return _build(check=args.check)
