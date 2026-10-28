"""CLI entry point for uncoded."""

import argparse
import shlex
import sys
from pathlib import Path

from uncoded import __version__
from uncoded.body import resolve_body
from uncoded.config import (
    UNCODED_TOML,
    Config,
    ConfigError,
    find_config,
    is_inside_project,
    read_config,
    render_conventional_config,
    validate_root,
)
from uncoded.docs_map import build_docs_map, read_doc_files, render_docs_map
from uncoded.extract import extract_modules, read_source_files
from uncoded.markers import GENERATED_MARKER
from uncoded.namespace_map import build_map, render_map
from uncoded.read_helpers import SkippedFile
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFoundError, UnsupportedNamePathError
from uncoded.skill import SKILL_ROOTS, agent_instructions, sync_skills
from uncoded.stubs import build_stubs, remove_all_stubs
from uncoded.sync import FileSyncError, remove_file, sync_file


def _warn_skipped(*, skipped: list[SkippedFile]) -> None:
    """Warn on standard error about each file that could not be indexed.

    Ends with a line that counts the skipped files, so that a skip is seen
    even when the warnings above it scroll by. Standard output is flushed
    first, so that the warnings follow the lines that name the files
    written, even when both streams go to one pipe, as in a pre-commit hook.
    """
    sys.stdout.flush()
    for skipped_file in skipped:
        print(
            f"warning: skipping {skipped_file.path}: {skipped_file.reason}",
            file=sys.stderr,
        )
    if skipped:
        print(f"warning: skipped {len(skipped)} file(s)", file=sys.stderr)


def _sync_code_artefacts(
    *, source_roots: list[Path], project_root: Path, check: bool
) -> tuple[int, list[SkippedFile]]:
    """Build or remove the code artefacts (namespace map and stubs).

    With no source roots, removes namespace.yaml and all stubs. Otherwise
    collects the source files beneath the resolved ``source_roots`` and writes
    the namespace map and stub files. Returns the change count and the files
    that could not be read or parsed.
    """
    if not source_roots:
        n = remove_file(
            path=Path(".uncoded/namespace.yaml"), project_root=project_root, check=check
        )
        n += remove_all_stubs(
            output_dir=Path(".uncoded/stubs"), project_root=project_root, check=check
        )
        return n, []

    roots_with_files = []
    all_skipped: list[SkippedFile] = []
    for src_root in source_roots:
        files, skipped = read_source_files(
            source_root=src_root, project_root=project_root
        )
        roots_with_files.append((src_root, files))
        all_skipped.extend(skipped)
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
    return n, all_skipped


def _sync_doc_artefacts(
    *, doc_roots: list[Path], project_root: Path, check: bool
) -> tuple[int, list[SkippedFile]]:
    """Build or remove the doc artefact (docs.yaml).

    With no doc roots, removes docs.yaml. Otherwise collects the Markdown files
    in the resolved ``doc_roots`` and writes docs.yaml. Returns the change
    count and the files that could not be read.
    """
    if not doc_roots:
        removed = remove_file(
            path=Path(".uncoded/docs.yaml"), project_root=project_root, check=check
        )
        return removed, []
    all_doc_files = []
    all_skipped: list[SkippedFile] = []
    for doc_root in doc_roots:
        files, skipped = read_doc_files(doc_root=doc_root, project_root=project_root)
        all_doc_files.extend(files)
        all_skipped.extend(skipped)
    docs_content = render_docs_map(mapping=build_docs_map(files=all_doc_files))
    changed = sync_file(
        path=Path(".uncoded/docs.yaml"),
        content=docs_content,
        project_root=project_root,
        check=check,
    )
    return changed, all_skipped


def _sync(*, config: Config, check: bool = False) -> int:
    """Sync (or verify) the index artefacts of the project that config configures.

    Every writer anchors the project-relative paths that it reads or writes at
    ``config.project_root``, so running from a subdirectory of the project
    produces artefacts in the same locations as running from the project
    directory.

    source-roots drive code artefacts (namespace.yaml, stubs); doc-roots
    drive doc artefacts (docs.yaml). Each root type is independent: when
    a root type is absent its artefacts are removed. Every root is checked
    before anything is written. Before writing any index artefact, sync writes
    .uncoded/.gitignore so the index stays local by default. Raises ConfigError
    when the configuration names no roots or a root cannot be used, and
    FileSyncError when a generated file cannot be read, written or removed. A
    file under a root that cannot be read or parsed is left out of the index
    and reported.

    When ``check=True``, the on-disk tree is not mutated; the function
    reports each prospective write or removal, returns 1 if anything
    would change, and 0 otherwise.
    """
    if not config.source_roots and not config.doc_roots:
        raise ConfigError(
            "nothing to index. "
            "Add source-roots or doc-roots to [tool.uncoded] in pyproject.toml, "
            "or as top-level keys in .uncoded.toml."
        )

    project_root = config.project_root
    source_roots = [
        validate_root(configured=configured, kind="source", config=config)
        for configured in config.source_roots
    ]
    doc_roots = [
        validate_root(configured=configured, kind="doc", config=config)
        for configured in config.doc_roots
    ]
    changes = sync_file(
        path=Path(".uncoded/.gitignore"),
        content=f"# {GENERATED_MARKER}\n*\n",
        project_root=project_root,
        check=check,
    )

    code_changes, code_skipped = _sync_code_artefacts(
        source_roots=source_roots, project_root=project_root, check=check
    )
    changes += code_changes
    changes += sync_skills(
        source=bool(source_roots),
        docs=bool(doc_roots),
        project_root=project_root,
        check=check,
    )
    doc_changes, doc_skipped = _sync_doc_artefacts(
        doc_roots=doc_roots, project_root=project_root, check=check
    )
    changes += doc_changes
    _warn_skipped(skipped=code_skipped + doc_skipped)

    if check:
        if changes:
            print(f"Index out of date: {changes} file(s) would change.")
            return 1
        print("Index is up to date.")
        return 0
    return 0


def _init(*, config: Config | None) -> int:
    """Set uncoded up in the project at the current directory, then sync it.

    With no configuration, writes a configuration file in the current directory
    naming the conventional roots. Leaves the configuration file of ``config``
    as it is, and says where it is. After the sync, says what to commit and
    prints the lines that tell agents to load the navigation skills. Returns 0.
    Raises ConfigError when there is no root to name or the sync fails, and
    FileSyncError when the configuration file cannot be written or a generated
    file cannot be read, written or removed.
    """
    if config is None:
        start = Path.cwd()
        content = render_conventional_config(
            directory=start, required_version=__version__
        )
        sync_file(path=Path(UNCODED_TOML), content=content, project_root=start)
        config = read_config(start=start)
    else:
        print(
            f"Found the configuration file in {config.project_root.as_posix()}, "
            "and left it as it is."
        )

    _sync(config=config)

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


class _OutsideProjectError(Exception):
    """Raised when an ``--in`` file is outside the project directory."""


def _project_file(*, in_path: str, project_root: Path) -> Path:
    """Return the ``--in`` file, or raise _OutsideProjectError when it is outside."""
    target = Path(in_path)
    if not is_inside_project(path=target, project_root=project_root):
        raise _OutsideProjectError(
            f"outside the project directory {project_root.as_posix()}."
        )
    return target


# The failures of a lookup that `uncoded body` and `uncoded refs` report, each
# with its message in _report_lookup_error.
_LOOKUP_ERRORS = (
    _OutsideProjectError,
    UnsupportedNamePathError,
    SymbolNotFoundError,
    OSError,
    UnicodeDecodeError,
    SyntaxError,
)


def _report_lookup_error(*, exc: Exception, name_path: str, in_path: str) -> int:
    """Print the CLI error message for a lookup failure and return 1.

    Covers the error arms that _body and _refs share.
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


def _body(*, config: Config, name_path: str, in_path: str) -> int:
    """Print the source body of name_path in in_path to stdout.

    Returns 0 on success. Returns 1 if in_path is outside the project
    directory of ``config``, if name_path is unsupported, if name_path is not
    present in the file, if the file cannot be read (missing, unreadable, or
    undecodable), or if the source has a syntax error.
    """
    try:
        target = _project_file(in_path=in_path, project_root=config.project_root)
        body = resolve_body(name_path=NamePath.parse(raw=name_path), in_path=target)
    except _LOOKUP_ERRORS as e:
        return _report_lookup_error(exc=e, name_path=name_path, in_path=in_path)

    sys.stdout.write(body)
    return 0


def _refs(*, config: Config, name_path: str, in_path: str) -> int:
    """Find all references to name_path in in_path and print them to stdout.

    ty reads the project directory of ``config`` as its workspace.

    Returns 0 on success. Each reference is printed as path:line:col.
    Returns 1 if in_path is outside the project directory, if name_path is
    unsupported, if name_path is not present in the file, if the file cannot
    be read (missing, unreadable, or undecodable), if the source has a syntax
    error, or if the reference lookup fails.
    """
    try:
        refs = find_refs(
            name_path=NamePath.parse(raw=name_path),
            in_path=_project_file(in_path=in_path, project_root=config.project_root),
            project_root=config.project_root,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except _LOOKUP_ERRORS as e:
        return _report_lookup_error(exc=e, name_path=name_path, in_path=in_path)

    for ref in refs:
        print(f"{ref.path.as_posix()}:{ref.line}:{ref.col}")
    return 0


def _check_required_version(*, config: Config | None, arguments: list[str]) -> None:
    """Raise ConfigError when the project requires another version of uncoded.

    The message gives ``arguments`` again, as the command that runs the
    required version. Without a project, or with no required version set,
    every version may run.
    """
    if config is None or config.required_version in (None, __version__):
        return
    required = config.required_version
    raise ConfigError(
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

    Each subparser binds how it finds the configuration and the action it
    runs on it.
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
    init_parser.set_defaults(find_project=find_config, action=_init)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Build or refresh generated navigation artefacts.",
    )
    sync_parser.set_defaults(
        find_project=read_config,
        action=lambda *, config: _sync(config=config, check=False),
    )

    check_parser = subparsers.add_parser(
        "check",
        help=(
            "Verify the index is up to date without writing. Exits non-zero "
            "if any file would change."
        ),
    )
    check_parser.set_defaults(
        find_project=read_config,
        action=lambda *, config: _sync(config=config, check=True),
    )

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
        find_project=read_config,
        action=lambda *, config: _body(
            config=config, name_path=args.name_path, in_path=args.in_path
        ),
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
        find_project=read_config,
        action=lambda *, config: _refs(
            config=config, name_path=args.name_path, in_path=args.in_path
        ),
    )

    arguments = sys.argv[1:]
    args = parser.parse_args(arguments)
    try:
        config = args.find_project(start=Path.cwd())
        _check_required_version(config=config, arguments=arguments)
        return args.action(config=config)
    except (ConfigError, FileSyncError) as e:
        # The error follows the lines that name the files already written,
        # even when both streams go to one pipe.
        sys.stdout.flush()
        print(f"Error: {e}", file=sys.stderr)
        return 1
