"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.config import (
    find_pyproject_toml,
    read_instruction_files,
    read_source_roots,
)
from uncoded.extract import iter_source_files, walk_source
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.serena_setup import setup
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs
from uncoded.sync import sync_file

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def _sync(*, root: Path | None = None, check: bool = False) -> int:
    """Sync (or verify) the namespace map, stub files, and instruction-file sections.

    ``root`` is the directory the upward walk for ``pyproject.toml``
    begins from; the parent of the located ``pyproject.toml`` becomes
    the project anchor used to resolve every project-relative input —
    source-root paths, instruction-file paths, and the rel-paths
    rendered into the namespace map and stubs. Defaults to the current
    working directory at the CLI boundary. Threading ``root`` through
    (rather than implicitly fetching cwd at each downstream call site)
    keeps every working-directory dependency visible in the signature
    and makes ``_sync`` testable against arbitrary trees.

    When ``check=True``, the on-disk tree is not mutated: each step reports
    whether it would write. Returns 1 if any step reports a prospective
    change (so CI can gate on a stale index), 0 if the tree is already in
    sync. In apply mode, returns 0 on success or 1 on configuration error.
    """
    if root is None:
        root = Path.cwd()

    pyproject_path = find_pyproject_toml(root)
    if pyproject_path is None:
        print(
            "Error: No pyproject.toml found. "
            "Add [tool.uncoded] source-roots to configure.",
            file=sys.stderr,
        )
        return 1
    project_root = pyproject_path.parent

    try:
        source_roots = [
            (project_root / r).resolve() for r in read_source_roots(project_root)
        ]
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for src_root in source_roots:
        if not src_root.is_dir():
            print(f"Error: {src_root} is not a directory", file=sys.stderr)
            return 1

    changes = 0

    # Drive a single ``iter_source_files`` pass per source root and feed
    # both the namespace map and the stubs pipeline from one read. Without
    # this, each pipeline calls ``iter_source_files`` separately and a
    # syntax-erroring file produces two identical ``warning: skipping``
    # lines per ``uncoded sync`` invocation — the contract is one warning
    # per broken file per sync.
    roots_with_files = [
        (src_root, list(iter_source_files(src_root, base=project_root)))
        for src_root in source_roots
    ]

    modules = [
        m
        for src_root, files in roots_with_files
        for m in walk_source(src_root, base=project_root, files=files)
    ]
    map_content = render_map(build_map(modules))
    if sync_file(DEFAULT_MAP_OUTPUT, map_content, check=check):
        changes += 1

    for src_root, files in roots_with_files:
        changes += build_stubs(src_root, base=project_root, files=files, check=check)

    # Dedupe configured instruction paths by resolved (canonical) path.
    # Without this, if CLAUDE.md is a symlink to AGENTS.md, pass 1 writes
    # through the symlink and reports the alias name while pass 2 finds
    # the file already in sync and reports nothing — asymmetric output
    # that hides the actual write target. Resolving collapses both aliases
    # to the same canonical path, which we render relative to
    # ``project_root`` for the user-facing line (matching how source-root
    # paths resolve), falling back to the absolute resolved path when
    # the file lives outside ``project_root``.
    seen_resolved: set[Path] = set()
    for path in read_instruction_files(project_root):
        resolved = (project_root / path).resolve()
        if resolved in seen_resolved:
            continue
        seen_resolved.add(resolved)
        try:
            canonical = resolved.relative_to(project_root)
        except ValueError:
            canonical = resolved
        if sync_instruction_file(canonical, check=check):
            changes += 1

    if sync_skill(check=check):
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

    Three subcommands: ``sync`` builds or refreshes the navigation index;
    ``check`` verifies the index matches what a rebuild would produce
    (exits non-zero on drift, useful in CI); ``setup`` generates
    MCP and Claude Code config for the recommended Serena + ty LSP
    integration.

    Each subparser binds its own ``action`` callable via
    ``set_defaults``; ``main`` then dispatches via ``args.action()``.
    Adding a new subcommand is a local change at the registration site —
    no central dispatch ladder to update, and no silent fall-through if
    the binding is forgotten (``args.action`` will simply be missing).
    """
    parser = argparse.ArgumentParser(
        prog="uncoded",
        description="Build a navigation index for AI coding agents.",
    )
    subparsers = parser.add_subparsers(required=True)

    sync_parser = subparsers.add_parser(
        "sync",
        help=(
            "Build or refresh the namespace map, stub files, and "
            "instruction-file sections."
        ),
    )
    sync_parser.set_defaults(action=lambda: _sync(check=False))

    check_parser = subparsers.add_parser(
        "check",
        help=(
            "Verify the index is up to date without writing. Exits non-zero "
            "if any file would change. Useful in CI."
        ),
    )
    check_parser.set_defaults(action=lambda: _sync(check=True))

    setup_parser = subparsers.add_parser(
        "setup",
        help=(
            "Write .mcp.json, .serena/project.yml, and .claude/settings.json "
            "for the recommended Serena + ty LSP integration."
        ),
    )
    setup_parser.set_defaults(action=lambda: setup())

    args = parser.parse_args()
    return args.action()
