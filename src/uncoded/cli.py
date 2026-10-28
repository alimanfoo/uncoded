"""CLI entry point for uncoded."""

import argparse
import shlex
import sys
from pathlib import Path

from uncoded import __version__
from uncoded.body import resolve_body
from uncoded.config import (
    UNCODED_TOML,
    ConfigError,
    find_config,
    read_config,
    render_conventional_config,
    validate_root,
)
from uncoded.docs_map import build_docs_map, iter_doc_files, render_docs_map
from uncoded.extract import extract_modules, iter_source_files
from uncoded.markers import GENERATED_MARKER
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFoundError, UnsupportedNamePathError
from uncoded.skill import SKILL_ROOTS, agent_instructions, sync_skills
from uncoded.stubs import build_stubs, remove_all_stubs
from uncoded.sync import remove_file, sync_file


def _sync_code_artefacts(
    *,
    build: bool,
    configured_source_roots: list[Path],
    project_root: Path,
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
            path=Path(".uncoded/namespace.yaml"), project_root=project_root, check=check
        )
        n += remove_all_stubs(
            output_dir=Path(".uncoded/stubs"), project_root=project_root, check=check
        )
        return n

    source_roots = [
        validate_root(configured=configured, kind="source", project_root=project_root)
        for configured in configured_source_roots
    ]

    roots_with_files = [
        (
            src_root,
            list(iter_source_files(source_root=src_root, project_root=project_root)),
        )
        for src_root in source_roots
    ]
    modules = [
        m for _root, files in roots_with_files for m in extract_modules(files=files)
    ]
    map_content = render_map(namespace=build_map(modules=modules))
    n = sync_file(
        path=Path(".uncoded/namespace.yaml"),
        content=map_content,
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
    check: bool,
) -> int:
    """Build or remove the doc artefact (docs.yaml).

    When build is False, removes docs.yaml and returns the change count. When
    build is True, validates, collects doc files, and writes docs.yaml. Returns
    the change count. Raises ConfigError on a validation failure.
    """
    if not build:
        return remove_file(
            path=Path(".uncoded/docs.yaml"), project_root=project_root, check=check
        )
    doc_roots = [
        validate_root(configured=configured, kind="doc", project_root=project_root)
        for configured in configured_doc_roots
    ]
    all_doc_files = [
        f
        for dr in doc_roots
        for f in iter_doc_files(doc_root=dr, project_root=project_root)
    ]
    docs_content = render_docs_map(mapping=build_docs_map(files=all_doc_files))
    return sync_file(
        path=Path(".uncoded/docs.yaml"),
        content=docs_content,
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
    a root type is absent its artefacts are removed. Before writing any index
    artefact, sync writes .uncoded/.gitignore so the index stays local by
    default. At least one root type must be configured.

    When ``check=True``, the on-disk tree is not mutated; the function
    reports each prospective write or removal, returns 1 if anything
    would change, and 0 otherwise. Configuration errors return 1.
    """
    if start is None:
        start = Path.cwd()

    try:
        config = read_config(start=start)
        if not config.source_roots and not config.doc_roots:
            raise ConfigError(
                "nothing to index. "
                "Add source-roots or doc-roots to [tool.uncoded] in pyproject.toml, "
                "or as top-level keys in .uncoded.toml."
            )

        project_root = config.project_root
        changes = sync_file(
            path=Path(".uncoded/.gitignore"),
            content=f"# {GENERATED_MARKER}\n*\n",
            project_root=project_root,
            check=check,
        )

        # Code artefacts — build when source_roots configured, else remove.
        changes += _sync_code_artefacts(
            build=bool(config.source_roots),
            configured_source_roots=config.source_roots,
            project_root=project_root,
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


def _init() -> int:
    """Set uncoded up in the project at the current directory, then sync it.

    With no configuration file found from the current directory, writes one
    there naming the conventional roots. Leaves a configuration file it finds
    as it is, and says where it is. After the sync, says what to commit and
    prints the lines that tell agents to load the navigation skills. Returns 1
    when there is no root to name or the sync fails, and 0 otherwise.
    """
    start = Path.cwd()
    config = find_config(start=start)
    if config is None:
        try:
            content = render_conventional_config(
                directory=start, required_version=__version__
            )
        except ConfigError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        sync_file(path=Path(UNCODED_TOML), content=content, project_root=start)
    else:
        print(
            f"Found the configuration file in {config.project_root.as_posix()}, "
            "and left it as it is."
        )

    if _sync(start=start) != 0:
        return 1

    config = read_config(start=start)
    skill_dirs = " and ".join(root.as_posix() for root in SKILL_ROOTS)
    instructions = agent_instructions(
        source=bool(config.source_roots), docs=bool(config.doc_roots)
    )
    print(
        f"\nCommit the configuration file and the installed skill files in "
        f"{skill_dirs}.\n\n"
        f"Add these lines to AGENTS.md or CLAUDE.md, so that agents load the "
        f"navigation skills at the start of every session. Without them, agents "
        f"load the uncoded skills only when they choose to.\n\n{instructions}",
        end="",
    )
    return 0


# The failures of a lookup that `uncoded body` and `uncoded refs` report, each
# with its message in _report_lookup_error. OSError covers FileNotFoundError.
_LOOKUP_ERRORS = (
    UnsupportedNamePathError,
    SymbolNotFoundError,
    OSError,
    UnicodeDecodeError,
    SyntaxError,
)


def _report_lookup_error(*, exc: Exception, name_path: str, in_path: str) -> int:
    """Print the CLI error message for a lookup failure and return 1.

    Covers the four shared error arms for _body and _refs: unsupported name
    path, symbol not found, file not found, and read/parse error.
    FileNotFoundError is checked before OSError because it subclasses it.
    """
    shown_path = Path(in_path).as_posix()
    if isinstance(exc, UnsupportedNamePathError):
        print(f"Error: {exc}", file=sys.stderr)
    elif isinstance(exc, SymbolNotFoundError):
        print(f"Error: {name_path!r} not found in {shown_path}", file=sys.stderr)
    elif isinstance(exc, FileNotFoundError):
        print(f"Error: {shown_path}: file not found.", file=sys.stderr)
    else:
        print(f"Error: {shown_path}: {exc}", file=sys.stderr)
    return 1


def _body(*, name_path: str, in_path: str) -> int:
    """Print the source body of name_path in in_path to stdout.

    Returns 0 on success. Returns 1 if name_path is unsupported, if
    name_path is not present in the file, if the file cannot be read
    (missing, unreadable, or undecodable), or if the source has a syntax error.
    """
    target = Path(in_path)
    try:
        body = resolve_body(name_path=NamePath.parse(raw=name_path), in_path=target)
    except _LOOKUP_ERRORS as e:
        return _report_lookup_error(exc=e, name_path=name_path, in_path=in_path)

    sys.stdout.write(body)
    return 0


def _refs(*, name_path: str, in_path: str) -> int:
    """Find all references to name_path in in_path and print them to stdout.

    Returns 0 on success. Each reference is printed as path:line:col.
    Returns 1 if name_path is unsupported, if name_path is not present in
    the file, if the file cannot be read (missing, unreadable, or
    undecodable), if the source has a syntax error, or if the reference
    lookup fails.
    """
    try:
        refs = find_refs(name_path=NamePath.parse(raw=name_path), in_path=Path(in_path))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except _LOOKUP_ERRORS as e:
        return _report_lookup_error(exc=e, name_path=name_path, in_path=in_path)

    for ref in refs:
        print(f"{ref.path.as_posix()}:{ref.line}:{ref.col}")
    return 0


def _refusal(*, arguments: list[str]) -> str | None:
    """Return why no command may run in the current project, or None.

    A command may not run when two files in one directory both configure
    uncoded, or when the project's required version is not the running
    version. The refusal for a version gives ``arguments`` again, as the
    command that runs the required version. Outside a project, or with no
    required version set, every command may run.
    """
    try:
        config = find_config(start=Path.cwd())
    except ConfigError as e:
        return str(e)
    if config is None or config.required_version in (None, __version__):
        return None
    required = config.required_version
    return (
        f"the project requires uncoded {required}, and this is uncoded "
        f"{__version__}. Run the command at the required version: "
        f"uvx uncoded@{required} {shlex.join(arguments)}"
    )


def main() -> int:
    """Dispatch the uncoded CLI.

    Five subcommands:

    - ``init`` — sets uncoded up in a project, then syncs its index.
    - ``sync`` — builds or refreshes the navigation index.
    - ``check`` — verifies the index matches what a rebuild would produce;
      exits non-zero on drift.
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
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Set uncoded up in a project, then build its index and skills.",
    )
    init_parser.set_defaults(action=_init)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Build or refresh generated navigation artefacts.",
    )
    sync_parser.set_defaults(action=lambda: _sync(check=False))

    check_parser = subparsers.add_parser(
        "check",
        help=(
            "Verify the index is up to date without writing. Exits non-zero "
            "if any file would change."
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

    arguments = sys.argv[1:]
    args = parser.parse_args(arguments)
    refusal = _refusal(arguments=arguments)
    if refusal is not None:
        print(f"Error: {refusal}", file=sys.stderr)
        return 1
    return args.action()
