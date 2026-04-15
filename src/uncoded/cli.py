"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.extract import walk_source
from uncoded.namespace_map import build_map, render_map
from uncoded.stubs import DEFAULT_STUBS_OUTPUT, build_stubs, generate_stubs

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Generate code navigation indexes for AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    for name, help_text in [
        ("sync", "Generate namespace map and stub files"),
        ("check", "Check that namespace map and stub files are up to date"),
    ]:
        subparsers.add_parser(name, help=help_text).add_argument(
            "source_roots", type=Path, nargs="+", metavar="source_root",
            help="Path(s) to source root(s) (e.g. src tests)",
        )

    args = parser.parse_args(argv)

    if args.command == "sync":
        return cmd_sync(args)

    if args.command == "check":
        return cmd_check(args)

    parser.print_help()
    return 1


def _resolve_source_roots(args: argparse.Namespace) -> list[Path] | None:
    roots = []
    for p in args.source_roots:
        resolved = p.resolve()
        if not resolved.is_dir():
            print(f"Error: {resolved} is not a directory", file=sys.stderr)
            return None
        roots.append(resolved)
    return roots


def cmd_sync(args: argparse.Namespace) -> int:
    source_roots = _resolve_source_roots(args)
    if source_roots is None:
        return 1

    modules = [m for root in source_roots for m in walk_source(root)]
    map_content = render_map(build_map(modules))
    DEFAULT_MAP_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_MAP_OUTPUT.write_text(map_content)
    print(f"Wrote {DEFAULT_MAP_OUTPUT}")

    for root in source_roots:
        build_stubs(root)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    source_roots = _resolve_source_roots(args)
    if source_roots is None:
        return 1

    ok = True

    modules = [m for root in source_roots for m in walk_source(root)]
    expected_map = render_map(build_map(modules))
    if not DEFAULT_MAP_OUTPUT.exists():
        print(f"Missing: {DEFAULT_MAP_OUTPUT}")
        ok = False
    elif DEFAULT_MAP_OUTPUT.read_text() != expected_map:
        print(f"Out of date: {DEFAULT_MAP_OUTPUT}")
        ok = False

    for root in source_roots:
        for rel_stub_path, expected_content in generate_stubs(root).items():
            stub_path = DEFAULT_STUBS_OUTPUT / rel_stub_path
            if not stub_path.exists():
                print(f"Missing: {stub_path}")
                ok = False
            elif stub_path.read_text() != expected_content:
                print(f"Out of date: {stub_path}")
                ok = False

    if not ok:
        print("Run `uncoded sync <src> [...]` to update.", file=sys.stderr)
        return 1

    return 0
