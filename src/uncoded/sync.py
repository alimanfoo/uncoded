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


def sync_file(path: Path, content: str, *, check: bool = False) -> bool:
    """Write ``content`` to ``path`` if it differs from what's on disk.

    Prints ``Wrote``/``Updated`` in apply mode, ``Would write``/``Would
    update`` in check mode. Returns ``True`` if a write was (or would be)
    performed, ``False`` if the file was already up to date. Parent
    directories are created as needed.
    """
    if not path.exists():
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        print(f"{'Would write' if check else 'Wrote'} {path}")
        return True
    if path.read_text() == content:
        return False
    if not check:
        path.write_text(content)
    print(f"{'Would update' if check else 'Updated'} {path}")
    return True


def remove_file(path: Path, *, check: bool = False) -> bool:
    """Remove ``path`` if it exists.

    Prints ``Removed`` in apply mode, ``Would remove`` in check mode.
    Returns ``True`` if a removal was (or would be) performed, ``False``
    if the file was already absent.
    """
    if not path.exists():
        return False
    if not check:
        path.unlink()
    print(f"{'Would remove' if check else 'Removed'} {path}")
    return True
