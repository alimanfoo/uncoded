"""File-reading helpers shared by sync iterators."""

import sys
from pathlib import Path


def _read_file_text_as_utf8(
    path: Path, *, display: Path | str | None = None
) -> str | None:
    """Read *path* as UTF-8 text.

    Returns None and prints a one-line warning to stderr when the file is
    unreadable or contains non-UTF-8 bytes, so callers can skip-and-continue
    without aborting the whole sync.

    *display* overrides the path shown in the warning message; pass a
    project-relative path so the warning matches the format used for other
    skip messages in the same iterator.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        label = display if display is not None else path
        print(f"warning: skipping {label}: {e}", file=sys.stderr)
        return None
