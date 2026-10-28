"""File-reading helpers for Python source and Markdown document reads."""

import sys
import tokenize
from pathlib import Path


def read_source_text(*, path: Path) -> str:
    """Read a Python source file under its declared PEP 263 encoding.

    Uses tokenize.open, which detects the encoding from a PEP 263 cookie or
    BOM and defaults to UTF-8. Raises OSError if the file cannot be opened,
    UnicodeDecodeError if the bytes don't match the declared or default
    encoding, and SyntaxError if the coding cookie is malformed or names an
    unknown codec (tokenize.open re-raises codec lookup failures as
    SyntaxError). The OSError and the SyntaxError name the file with ``/``
    separators, on Windows too, because the file is opened by that form of
    its path.
    """
    with tokenize.open(path.as_posix()) as f:
        return f.read()


def read_source_text_or_warn(*, path: Path, warning_path: str) -> str | None:
    """Read a Python source file, returning None and warning to stderr on failure.

    Wraps read_source_text and catches OSError, UnicodeDecodeError, and
    SyntaxError. Prints a "warning: skipping ..." line to
    stderr and returns None so callers can skip-and-continue without aborting
    the whole sync.

    warning_path is the path shown in the warning message. Pass the
    project-relative path with ``/`` separators, so the warning matches the
    other skip messages in the same iterator.
    """
    try:
        return read_source_text(path=path)
    except (OSError, UnicodeDecodeError, SyntaxError) as e:
        print(f"warning: skipping {warning_path}: {_reason(error=e)}", file=sys.stderr)
        return None


def read_doc_text_or_warn(*, path: Path, warning_path: str) -> str | None:
    """Read a Markdown document as UTF-8, returning None and warning on failure.

    Strips a leading UTF-8 BOM on read. Files without a BOM are unaffected.

    Returns None and prints a one-line warning to stderr when the file is
    unreadable or contains non-UTF-8 bytes, so callers can skip-and-continue
    without aborting the whole sync.

    warning_path is the path shown in the warning message. Pass the
    project-relative path with ``/`` separators, so the warning matches the
    other skip messages in the same iterator.
    """
    try:
        return path.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError) as e:
        print(f"warning: skipping {warning_path}: {_reason(error=e)}", file=sys.stderr)
        return None


def _reason(*, error: Exception) -> str:
    # The warning names the file already. An OSError from the system names it
    # again, by its absolute path in the system's form, so give only the
    # reason. An OSError without one has only its own text.
    if isinstance(error, OSError):
        return error.strerror or str(error)
    return str(error)
