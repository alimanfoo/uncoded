"""Content-aware file writes with an optional check-only mode.

Every place that writes an artifact (namespace map, stubs, instruction-file
sections) routes through :func:`sync_file` / :func:`remove_file` so that two
concerns live in one place: only write when content actually changes, and
when ``check=True`` report the prospective action without touching disk.

``check=True`` is what powers ``uncoded --check`` — the same pipeline runs,
but the writers never mutate the tree, and the CLI exits non-zero if any
helper reports a change. That gives CI a zero-mutation freshness gate.
"""

from pathlib import Path


def sync_file(
    path: Path,
    content: str,
    *,
    root: Path | None = None,
    check: bool = False,
) -> bool:
    """Write ``content`` to ``path`` if it differs from what's on disk.

    Prints ``Wrote``/``Updated`` in apply mode, ``Would write``/``Would
    update`` in check mode. Returns ``True`` if a write was (or would be)
    performed, ``False`` if the file was already up to date. Parent
    directories are created as needed.

    When ``root`` is provided, ``path`` is treated as relative to ``root``
    for filesystem I/O while the printed message still names ``path`` as
    given. This lets callers anchor writes at a project root regardless of
    the current working directory while keeping log lines project-relative.
    Passing an absolute ``path`` makes ``root`` a no-op (the absolute side
    wins under ``Path``'s join semantics).
    """
    target = root / path if root is not None else path
    if not target.exists():
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        print(f"{'Would write' if check else 'Wrote'} {path}")
        return True
    if target.read_text() == content:
        return False
    if not check:
        target.write_text(content)
    print(f"{'Would update' if check else 'Updated'} {path}")
    return True


def remove_file(
    path: Path,
    *,
    root: Path | None = None,
    check: bool = False,
) -> bool:
    """Remove ``path`` if it exists.

    Prints ``Removed`` in apply mode, ``Would remove`` in check mode.
    Returns ``True`` if a removal was (or would be) performed, ``False``
    if the file was already absent.

    When ``root`` is provided, ``path`` is treated as relative to ``root``
    for filesystem I/O while the printed message still names ``path`` as
    given.
    """
    target = root / path if root is not None else path
    if not target.exists():
        return False
    if not check:
        target.unlink()
    print(f"{'Would remove' if check else 'Removed'} {path}")
    return True
