"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.config import (
    find_pyproject_toml,
    read_instruction_files,
    read_source_roots,
)
from uncoded.extract import extract_modules, iter_source_files
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.serena_setup import setup
from uncoded.skill import sync_skill
from uncoded.stubs import DEFAULT_STUBS_OUTPUT, _generate_stubs, _write_stubs
from uncoded.sync import sync_file

DEFAULT_MAP_OUTPUT = Path(".uncoded/namespace.yaml")


def _sync(*, root: Path | None = None, check: bool = False) -> int:
    """Sync (or verify) the namespace map, stub files, and instruction-file sections.

    ``root`` is the directory the upward walk for ``pyproject.toml``
    begins from; the parent of the located ``pyproject.toml`` becomes
    the project anchor for every project-relative path — both the
    *inputs* (source roots, instruction-file paths, the rel-paths
    rendered into the namespace map and stubs) and the *outputs*
    (``DEFAULT_MAP_OUTPUT``, ``DEFAULT_STUBS_OUTPUT``, the skill output
    paths, and the instruction-file write target). Defaults to the
    current working directory at the CLI boundary. Running from a
    subdirectory of the project produces artefacts in the same
    locations as running from the project root.

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
    except LookupError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for src_root in source_roots:
        if not src_root.is_dir():
            print(f"Error: {src_root} is not a directory", file=sys.stderr)
            return 1

    changes = 0

    roots_with_files = [
        (src_root, list(iter_source_files(src_root, base=project_root)))
        for src_root in source_roots
    ]

    modules = [
        m for _src_root, files in roots_with_files for m in extract_modules(files)
    ]
    map_content = render_map(build_map(modules))
    if sync_file(DEFAULT_MAP_OUTPUT, map_content, root=project_root, check=check):
        changes += 1

    for src_root, files in roots_with_files:
        stubs = _generate_stubs(files)
        changes += _write_stubs(
            stubs=stubs,
            source_root=src_root,
            output_dir=DEFAULT_STUBS_OUTPUT,
            base=project_root,
            root=project_root,
            check=check,
        )

    # Dedupe configured instruction paths by resolved (canonical) path.
    # Without this, if CLAUDE.md is a symlink to AGENTS.md, pass 1 writes
    # through the symlink and reports the alias name while pass 2 finds
    # the file already in sync and reports nothing — asymmetric output
    # that hides the actual write target. Resolving collapses both aliases
    # to the same canonical path, which we render relative to
    # ``project_root`` for the user-facing line, falling back to the
    # absolute resolved path when the file lives outside ``project_root``.
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
        if sync_instruction_file(canonical, root=project_root, check=check):
            changes += 1

    if sync_skill(root=project_root, check=check):
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
