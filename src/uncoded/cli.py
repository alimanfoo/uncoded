"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path
from typing import Literal

from uncoded.body import resolve_body
from uncoded.config import ConfigError, read_config
from uncoded.docs_map import build_docs_map, iter_doc_files, render_docs_map
from uncoded.extract import extract_modules, iter_source_files
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFound, UnsupportedNamePath
from uncoded.skill import sync_skills
from uncoded.stubs import build_stubs, remove_all_stubs
from uncoded.sync import remove_file, sync_file


def _validate_root(
    configured: Path,
    *,
    kind: Literal["source", "doc"],
    project_root: Path,
    resolved_project_root: Path,
    accepts_md_file: bool,
) -> Path:
    """Resolve configured against project_root and validate the result.

    Raises ConfigError if the resolved path falls outside the project root or
    is not a valid target. When accepts_md_file is True, a lone .md file is
    also valid. kind selects the noun used in the error messages.
    """
    resolved = (project_root / configured).resolve()
    if not resolved.is_relative_to(resolved_project_root):
        raise ConfigError(
            f"{kind} root {configured} is outside the project root. "
            f"Check {kind}-roots in your uncoded config file."
        )
    is_valid = resolved.is_dir() or (
        accepts_md_file and resolved.is_file() and resolved.suffix == ".md"
    )
    if not is_valid:
        if accepts_md_file:
            raise ConfigError(
                f"{kind} root {configured} is not a directory or .md file. "
                f"Check {kind}-roots in your uncoded config file."
            )
        raise ConfigError(
            f"{kind} root {configured} is not a directory. "
            f"Check {kind}-roots in your uncoded config file."
        )
    return resolved


def _sync_code_artefacts(
    *,
    build: bool,
    configured_source_roots: list[Path],
    project_root: Path,
    resolved_project_root: Path,
    check: bool,
) -> int:
    """Build or remove the code artefacts (namespace map and stubs).

    When build is False, removes namespace.yaml and all stubs and returns the
    change count. When build is True, validates, collects source files, and
    writes the namespace map and stub files. Returns the change count. Raises
    ConfigError on a validation failure.
    """
    if not build:
        n = remove_file(
            Path(".uncoded/namespace.yaml"), project_root=project_root, check=check
        )
        n += remove_all_stubs(
            Path(".uncoded/stubs"), project_root=project_root, check=check
        )
        return n

    source_roots = [
        _validate_root(
            configured,
            kind="source",
            project_root=project_root,
            resolved_project_root=resolved_project_root,
            accepts_md_file=False,
        )
        for configured in configured_source_roots
    ]

    roots_with_files = [
        (src_root, list(iter_source_files(src_root, project_root=project_root)))
        for src_root in source_roots
    ]
    modules = [m for _root, files in roots_with_files for m in extract_modules(files)]
    map_content = render_map(build_map(modules))
    n = sync_file(
        Path(".uncoded/namespace.yaml"),
        map_content,
        project_root=project_root,
        check=check,
    )
    for src_root, files in roots_with_files:
        n += build_stubs(
            files=files,
            source_root=src_root,
            output_dir=Path(".uncoded/stubs"),
            project_root=project_root,
            check=check,
        )
    return n


def _sync_doc_artefacts(
    *,
    build: bool,
    configured_doc_roots: list[Path],
    project_root: Path,
    resolved_project_root: Path,
    check: bool,
) -> int:
    """Build or remove the doc artefact (docs.yaml).

    When build is False, removes docs.yaml and returns the change count. When
    build is True, validates, collects doc files, and writes docs.yaml. Returns
    the change count. Raises ConfigError on a validation failure.
    """
    if not build:
        return remove_file(
            Path(".uncoded/docs.yaml"), project_root=project_root, check=check
        )
    doc_roots = [
        _validate_root(
            configured,
            kind="doc",
            project_root=project_root,
            resolved_project_root=resolved_project_root,
            accepts_md_file=True,
        )
        for configured in configured_doc_roots
    ]
    all_doc_files = []
    for dr in doc_roots:
        all_doc_files.extend(iter_doc_files(dr, project_root))
    docs_content = render_docs_map(build_docs_map(all_doc_files))
    return sync_file(
        Path(".uncoded/docs.yaml"),
        docs_content,
        project_root=project_root,
        check=check,
    )


def _sync(*, start: Path | None = None, check: bool = False) -> int:
    """Sync (or verify) the index artefacts for each configured root type.

    The upward walk for the config file begins at ``start`` (defaulting
    to the current working directory at the CLI boundary). The parent of
    the located config file becomes ``project_root``: the single anchor
    every writer uses for project-relative paths it reads or writes.
    Running from a subdirectory of the project produces artefacts in the
    same locations as running from the project root.

    source-roots drive code artefacts (namespace.yaml, stubs); doc-roots
    drive doc artefacts (docs.yaml). Each root type is independent: when
    a root type is absent its artefacts are removed. At least one root
    type must be configured.

    When ``check=True``, the on-disk tree is not mutated; the function
    reports each prospective write or removal, returns 1 if anything
    would change, and 0 otherwise. Configuration errors return 1.
    """
    if start is None:
        start = Path.cwd()

    try:
        config = read_config(start)
        if not config.source_roots and not config.doc_roots:
            raise ConfigError(
                "nothing to index. "
                "Add source-roots or doc-roots to [tool.uncoded] in pyproject.toml, "
                "or as top-level keys in .uncoded.toml."
            )

        project_root = config.project_root
        resolved_project_root = project_root.resolve()
        changes = 0

        # Code artefacts — build when source_roots configured, else remove.
        changes += _sync_code_artefacts(
            build=bool(config.source_roots),
            configured_source_roots=config.source_roots,
            project_root=project_root,
            resolved_project_root=resolved_project_root,
            check=check,
        )
        changes += sync_skills(
            source=bool(config.source_roots),
            docs=bool(config.doc_roots),
            project_root=project_root,
            check=check,
        )
        # Doc artefacts — build when doc_roots configured, else remove.
        changes += _sync_doc_artefacts(
            build=bool(config.doc_roots),
            configured_doc_roots=config.doc_roots,
            project_root=project_root,
            resolved_project_root=resolved_project_root,
            check=check,
        )
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if check:
        if changes:
            print(f"Index out of date: {changes} file(s) would change.")
            return 1
        print("Index is up to date.")
        return 0
    return 0


def _report_lookup_error(exc: Exception, *, name_path: str, in_path: str) -> int:
    """Print the CLI error message for a lookup failure and return 1.

    Covers the four shared error arms for _body and _refs: unsupported name
    path, symbol not found, file not found, and read/parse error.
    FileNotFoundError is checked before OSError because it subclasses it.
    """
    if isinstance(exc, UnsupportedNamePath):
        print(f"Error: {exc}", file=sys.stderr)
    elif isinstance(exc, SymbolNotFound):
        print(f"Error: {name_path!r} not found in {in_path}", file=sys.stderr)
    elif isinstance(exc, FileNotFoundError):
        print(f"Error: {in_path}: file not found.", file=sys.stderr)
    else:
        print(f"Error: {in_path}: {exc}", file=sys.stderr)
    return 1


def _body(*, name_path: str, in_path: str) -> int:
    """Print the source body of name_path in in_path to stdout.

    Returns 0 on success. Returns 1 if name_path is unsupported, if
    name_path is not present in the file, if the file cannot be read
    (missing, unreadable, or undecodable), or if the source has a syntax error.
    """
    target = Path(in_path)
    try:
        body = resolve_body(NamePath.parse(name_path), target)
    except (
        UnsupportedNamePath,
        SymbolNotFound,
        FileNotFoundError,
        OSError,
        UnicodeDecodeError,
        SyntaxError,
    ) as e:
        return _report_lookup_error(e, name_path=name_path, in_path=in_path)

    sys.stdout.write(body)
    return 0


def _refs(*, name_path: str, in_path: str) -> int:
    """Find all references to name_path in in_path and print them to stdout.

    Returns 0 on success. Each reference is printed as rel_path:line:col.
    Returns 1 if name_path is unsupported, if name_path is not present in
    the file, if the file cannot be read (missing, unreadable, or
    undecodable), if the source has a syntax error, or if the reference
    lookup fails.
    """
    try:
        refs = find_refs(NamePath.parse(name_path), Path(in_path))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (
        UnsupportedNamePath,
        SymbolNotFound,
        FileNotFoundError,
        OSError,
        UnicodeDecodeError,
        SyntaxError,
    ) as e:
        return _report_lookup_error(e, name_path=name_path, in_path=in_path)

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
        help=("Build or refresh the namespace map, stub files, and skill files."),
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
