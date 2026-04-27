# src/uncoded/sync.py

from pathlib import Path

def sync_file(path: Path, content: str, *, check: bool) -> bool:
    """Write ``content`` to ``path`` if it differs from what's on disk."""
    ...

def remove_file(path: Path, *, check: bool) -> bool:
    """Remove ``path`` if it exists."""
    ...
