"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.body import resolve_body
from uncoded.config import (
    find_pyproject_toml,
    read_instruction_files,
    read_source_roots,
)
from uncoded.extract import extract_modules, iter_source_files
from uncoded.instruction_files import sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFound, UnsupportedNamePath
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs
from uncoded.sync import sync_file


def _find_project_root(*, start: Path) -> Path | None:
    """Return the project root for start, or None if no pyproject.toml is found.

    Prints the error message to stderr before returning None so the caller
    only needs to check the return value and return 1.
    """
    pyproject_path = find_pyproject_toml(start)
    if pyproject_path is None:
        print(
            "Error: No pyproject.toml found. "
            "Create one with a [tool.uncoded] source-roots entry.",
            file=sys.stderr,
        )
        return None
    return pyproject_path.parent


def _sync(*, start: Path | None = None, check: bool = False) -> int:
    """Sync (or verify) the namespace map, stub files, and instruction-file sections.

    The upward walk for ``pyproject.toml`` begins at ``start`` (defaulting
    to the current working directory at the CLI boundary). The parent of
    the located ``pyproject.toml`` becomes ``project_root``: the single
    anchor every writer uses for project-relative paths it reads or
    writes. Running from a subdirectory of the project produces artefacts
    in the same locations as running from the project root.

    When ``check=True``, the on-disk tree is not mutated; the function
    reports each prospective write, returns 1 if anything would change
    (so CI can gate on a stale index), and 0 otherwise. Configuration
    errors return 1 in either mode.
    """
    if start is None:
        start = Path.cwd()

    project_root = _find_project_root(start=start)
    if project_root is None:
        return 1

    try:
        configured_roots = read_source_roots(project_root / "pyproject.toml")
    except LookupError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    source_roots: list[Path] = []
    for configured in configured_roots:
        src_root = (project_root / configured).resolve()
        if not src_root.is_dir():
            print(
                f"Error: source root {configured} is not a directory. "
                "Check [tool.uncoded] source-roots in pyproject.toml.",
                file=sys.stderr,
            )
            return 1
        source_roots.append(src_root)

    changes = 0

    roots_with_files = [
        (src_root, list(iter_source_files(src_root, project_root=project_root)))
        for src_root in source_roots
    ]

    modules = [
        m for _src_root, files in roots_with_files for m in extract_modules(files)
    ]
    map_content = render_map(build_map(modules))
    if sync_file(
        Path(".uncoded/namespace.yaml"),
        map_content,
        project_root=project_root,
        check=check,
    ):
        changes += 1

    for src_root, files in roots_with_files:
        changes += build_stubs(
            files=files,
            source_root=src_root,
            output_dir=Path(".uncoded/stubs"),
            project_root=project_root,
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
        if sync_instruction_file(canonical, project_root=project_root, check=check):
            changes += 1

    if sync_skill(project_root=project_root, check=check):
        changes += 1

    if check:
        if changes:
            print(f"Index out of date: {changes} file(s) would change.")
            return 1
        print("Index is up to date.")
        return 0
    return 0


def _body(*, name_path: str, in_path: str) -> int:
    """Print the source body of name_path in in_path to stdout.

    Returns 0 on success. Returns 1 if name_path is unsupported, if
    name_path is not present in the file, if the file does not exist,
    or if the file has a syntax error.
    """
    target = Path(in_path)
    try:
        body = resolve_body(NamePath.parse(name_path), target)
    except UnsupportedNamePath as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SymbolNotFound:
        print(f"Error: {name_path!r} not found in {in_path}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: {in_path}: file not found.", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Error: {in_path}: {e}", file=sys.stderr)
        return 1

    sys.stdout.write(body)
    return 0


def _refs(*, name_path: str, in_path: str) -> int:
    """Find all references to name_path in in_path and print them to stdout.

    Returns 0 on success. Each reference is printed as rel_path:line:col.
    Returns 1 on any error.
    """
    # resolve() is required: _query_references calls Path.as_uri(), which
    # raises ValueError on a relative path.
    target = Path(in_path).resolve()
    try:
        refs = find_refs(NamePath.parse(name_path), target)
    except UnsupportedNamePath as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except SymbolNotFound:
        print(f"Error: {name_path!r} not found in {in_path}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: {in_path}: file not found.", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Error: {in_path}: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for ref in refs:
        print(f"{ref.rel_path}:{ref.line}:{ref.col}")
    return 0


def main() -> int:
    """Dispatch the uncoded CLI.

    Four subcommands:

    - ``sync`` — builds or refreshes the navigation index.
    - ``check`` — verifies the index matches what a rebuild would produce;
      exits non-zero on drift, useful in CI.
    - ``body`` — prints the source body of a named symbol to stdout.
    - ``refs`` — finds all references to a named symbol and prints them.

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

    body_parser = subparsers.add_parser(
        "body",
        help="Print the source body of a named symbol to stdout.",
    )
    body_parser.add_argument(
        "name_path",
        help="Symbol path: one segment for top-level, two for Class/member.",
    )
    body_parser.add_argument(
        "--in",
        dest="in_path",
        required=True,
        metavar="PATH",
        help="Source file path (relative to current directory).",
    )
    body_parser.set_defaults(
        action=lambda: _body(name_path=args.name_path, in_path=args.in_path)
    )

    refs_parser = subparsers.add_parser(
        "refs",
        help="Find all references to a named symbol and print them to stdout.",
    )
    refs_parser.add_argument(
        "name_path",
        help="Symbol path: one segment for top-level, two for Class/member.",
    )
    refs_parser.add_argument(
        "--in",
        dest="in_path",
        required=True,
        metavar="PATH",
        help="Source file path (relative to current directory).",
    )
    refs_parser.set_defaults(
        action=lambda: _refs(name_path=args.name_path, in_path=args.in_path)
    )

    args = parser.parse_args()
    return args.action()
