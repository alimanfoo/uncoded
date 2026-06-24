"""File-reading helpers for Python source and Markdown document reads."""

import sys
import tokenize
from pathlib import Path


def read_source_text(path: Path) -> str:
    """Read a Python source file under its declared PEP 263 encoding.

    Uses tokenize.open, which detects the encoding from a PEP 263 cookie or
    BOM and defaults to UTF-8. Raises OSError if the file cannot be opened,
    UnicodeDecodeError if the bytes don't match the declared or default
    encoding, LookupError if the declared codec name is unknown, and
    SyntaxError if the coding cookie is malformed (for example, a BOM and
    cookie that disagree).
    """
    with tokenize.open(path) as f:
        return f.read()


def read_source_text_or_warn(
    path: Path, *, warning_path: Path | str | None = None
) -> str | None:
    """Read a Python source file, returning None and warning to stderr on failure.

    Wraps read_source_text and catches OSError, UnicodeDecodeError,
    LookupError, and SyntaxError. Prints a "warning: skipping ..." line to
    stderr and returns None so callers can skip-and-continue without aborting
    the whole sync.

    warning_path overrides the path shown in the warning message; pass a
    project-relative path so the warning matches the format used for other
    skip messages in the same iterator.
    """
    try:
        return read_source_text(path)
    except (OSError, UnicodeDecodeError, LookupError, SyntaxError) as e:
        label = warning_path if warning_path is not None else path
        print(f"warning: skipping {label}: {e}", file=sys.stderr)
        return None


def read_doc_text_or_warn(
    path: Path, *, warning_path: Path | str | None = None
) -> str | None:
    """Read a Markdown document as UTF-8, returning None and warning on failure.

    Returns None and prints a one-line warning to stderr when the file is
    unreadable or contains non-UTF-8 bytes, so callers can skip-and-continue
    without aborting the whole sync.

    warning_path overrides the path shown in the warning message; pass a
    project-relative path so the warning matches the format used for other
    skip messages in the same iterator.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        label = warning_path if warning_path is not None else path
        print(f"warning: skipping {label}: {e}", file=sys.stderr)
        return None
