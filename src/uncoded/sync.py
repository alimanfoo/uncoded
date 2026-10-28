"""Content-aware file writes with an optional check-only mode.

Every generated file routes through :func:`sync_file` or
:func:`remove_file`. The helpers write only when content changes. When
``check=True``, they report the prospective action without touching disk.

``check=True`` is what powers ``uncoded check``: the same pipeline runs, but
the writers never change the tree, and the CLI exits non-zero if any helper
reports a change. That gives a freshness check that changes nothing.

A file that cannot be read, written or removed raises
:class:`FileSyncError`, which names it.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from uncoded.read_helpers import failure_reason


class FileSyncError(Exception):
    """Raised when a file cannot be read, written or removed.

    The message names the file, relative to the project directory, what
    could not be done to it, and why.
    """


@contextmanager
def _naming_failure(*, action: str, path: Path) -> Generator[None]:
    """Turn a failure to ``action`` the file at ``path`` into a FileSyncError."""
    try:
        yield
    except (OSError, UnicodeDecodeError) as e:
        reason = failure_reason(error=e)
        raise FileSyncError(f"cannot {action} {path.as_posix()}: {reason}") from e


def sync_file(
    *,
    path: Path,
    content: str,
    project_root: Path,
    check: bool = False,
) -> bool:
    """Write ``content`` to ``path`` if it differs from what's on disk.

    Prints ``Wrote``/``Updated`` in apply mode, ``Would write``/``Would
    update`` in check mode. Returns ``True`` if a write was (or would be)
    performed, ``False`` if the file was already up to date. Parent
    directories are created as needed. Raises :class:`FileSyncError` when
    the file cannot be read or written.

    The file is written to ``project_root / path``. The log line still
    names ``path`` as given, so messages stay project-relative
    regardless of where the caller is running from.
    """
    target = project_root / path
    with _naming_failure(action="read", path=path):
        current = target.read_text(encoding="utf-8") if target.exists() else None
    if current == content:
        return False
    if not check:
        with _naming_failure(action="write", path=path):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    if current is None:
        print(f"{'Would write' if check else 'Wrote'} {path.as_posix()}")
        return True
    print(f"{'Would update' if check else 'Updated'} {path.as_posix()}")
    return True


def remove_file(
    *,
    path: Path,
    project_root: Path,
    check: bool = False,
) -> bool:
    """Remove ``path`` if it exists, and each parent directory left empty.

    Prints ``Removed`` in apply mode, ``Would remove`` in check mode.
    Returns ``True`` if a removal was (or would be) performed, ``False``
    if the file was already absent. Raises :class:`FileSyncError` when the
    file or a parent directory cannot be removed.

    As :func:`sync_file` creates each missing parent directory, the
    removal removes each parent directory that it leaves empty, up to
    but not including ``project_root``. It stops at a symbolic link.

    The file removed is ``project_root / path``. The log line still
    names ``path`` as given, so messages stay project-relative
    regardless of where the caller is running from.
    """
    target = project_root / path
    parents = target.relative_to(project_root).parents[:-1]
    with _naming_failure(action="remove", path=path):
        if not target.exists():
            return False
        if not check:
            target.unlink()
            for parent in parents:
                directory = project_root / parent
                if directory.is_symlink() or any(directory.iterdir()):
                    break
                directory.rmdir()
    print(f"{'Would remove' if check else 'Removed'} {path.as_posix()}")
    return True
