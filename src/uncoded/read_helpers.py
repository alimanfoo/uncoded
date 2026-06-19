"""File-reading helpers shared by sync iterators."""

import sys
from pathlib import Path


def _read_file_text(path: Path) -> str | None:
    """Read *path* as UTF-8 text.

    Returns None and prints a one-line warning to stderr when the file is
    unreadable or contains non-UTF-8 bytes, so callers can skip-and-continue
    without aborting the whole sync.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(f"warning: skipping {path}: {e}", file=sys.stderr)
        return None
