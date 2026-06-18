"""CLI entry point for uncoded."""

import argparse
import sys
from pathlib import Path

from uncoded.body import resolve_body
from uncoded.config import read_config
from uncoded.docs_map import build_docs_map, iter_doc_files, render_docs_map
from uncoded.extract import extract_modules, iter_source_files
from uncoded.instruction_files import SECTION_CODE, SECTION_DOCS, sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFound, UnsupportedNamePath
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs, remove_all_stubs
from uncoded.sync import remove_file, sync_file


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

    config = read_config(start)
    if config is None:
        print(
            "Error: No pyproject.toml or .uncoded.toml found. "
            "Create one to configure uncoded.",
            file=sys.stderr,
        )
        return 1

    if not config.source_roots and not config.doc_roots:
        print(
            "Error: nothing to index. "
            "Add source-roots or doc-roots to [tool.uncoded] in pyproject.toml, "
            "or as top-level keys in .uncoded.toml.",
            file=sys.stderr,
        )
        return 1

    project_root = config.project_root
    changes = 0

    # Code artefacts — build when source_roots configured, else remove.
    if config.source_roots:
        source_roots: list[Path] = []
        for configured in config.source_roots:
            src_root = (project_root / configured).resolve()
            if not src_root.is_dir():
                print(
                    f"Error: source root {configured} is not a directory. "
                    "Check source-roots in your uncoded config file.",
                    file=sys.stderr,
                )
                return 1
            source_roots.append(src_root)

        roots_with_files = [
            (src_root, list(iter_source_files(src_root, project_root=project_root)))
            for src_root in source_roots
        ]
        modules = [
            m for _root, files in roots_with_files for m in extract_modules(files)
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
    else:
        if remove_file(
            Path(".uncoded/namespace.yaml"), project_root=project_root, check=check
        ):
            changes += 1
        changes += remove_all_stubs(
            Path(".uncoded/stubs"),
            project_root=project_root,
            check=check,
        )

    # Doc artefacts — build when doc_roots configured, else remove.
    if config.doc_roots:
        doc_roots: list[Path] = []
        resolved_project_root = project_root.resolve()
        for configured in config.doc_roots:
            doc_root = (project_root / configured).resolve()
            if not doc_root.is_relative_to(resolved_project_root):
                print(
                    f"Error: doc root {configured} is outside the project root. "
                    "Check doc-roots in your uncoded config file.",
                    file=sys.stderr,
                )
                return 1
            is_valid = doc_root.is_dir() or (
                doc_root.is_file() and doc_root.suffix == ".md"
            )
            if not is_valid:
                print(
                    f"Error: doc root {configured} is not a directory or .md file. "
                    "Check doc-roots in your uncoded config file.",
                    file=sys.stderr,
                )
                return 1
            doc_roots.append(doc_root)

        all_doc_files = []
        for dr in doc_roots:
            all_doc_files.extend(iter_doc_files(dr, project_root))
        docs_content = render_docs_map(build_docs_map(all_doc_files))
        if sync_file(
            Path(".uncoded/docs.yaml"),
            docs_content,
            project_root=project_root,
            check=check,
        ):
            changes += 1
    else:
        if remove_file(
            Path(".uncoded/docs.yaml"), project_root=project_root, check=check
        ):
            changes += 1

    # Instruction sections — each present only when its root type is configured.
    code_section = SECTION_CODE if config.source_roots else None
    docs_section = SECTION_DOCS if config.doc_roots else None

    # Dedupe configured instruction paths by resolved (canonical) path.
    # Without this, if CLAUDE.md is a symlink to AGENTS.md, pass 1 writes
    # through the symlink and reports the alias name while pass 2 finds
    # the file already in sync and reports nothing — asymmetric output
    # that hides the actual write target. Resolving collapses both aliases
    # to the same canonical path, which we render relative to
    # ``project_root`` for the user-facing line, falling back to the
    # absolute resolved path when the file lives outside ``project_root``.
    seen_resolved: set[Path] = set()
    for path in config.instruction_files:
        resolved = (project_root / path).resolve()
        if resolved in seen_resolved:
            continue
        seen_resolved.add(resolved)
        try:
            canonical = resolved.relative_to(project_root)
        except ValueError:
            canonical = resolved
        if sync_instruction_file(
            canonical,
            code_section=code_section,
            docs_section=docs_section,
            project_root=project_root,
            check=check,
        ):
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
    try:
        refs = find_refs(NamePath.parse(name_path), Path(in_path))
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
