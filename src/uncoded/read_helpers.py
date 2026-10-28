"""File-reading helpers, and the record of a file that could not be used."""

import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkippedFile:
    """A file under a root that could not be read or parsed, and why.

    ``path`` is the file's path relative to the project directory, with
    ``/`` separators on every platform.
    """

    path: str
    reason: str


def read_source_text(*, path: Path) -> str:
    """Read a Python source file's text under its declared PEP 263 encoding.

    Uses tokenize.open, which detects the encoding from a PEP 263 cookie or
    BOM and defaults to UTF-8, and leaves the BOM out of the text. Keeps
    every line ending as it is in the file, so that a definition sliced from
    the text is exactly as it is in the file. Raises OSError if the file
    cannot be opened, UnicodeDecodeError if the bytes don't match the
    declared or default encoding, and SyntaxError if the coding cookie is
    malformed or names an unknown codec (tokenize.open re-raises codec
    lookup failures as SyntaxError). The OSError and the SyntaxError name the
    file with ``/`` separators, on Windows too, because the file is opened by
    that form of its path.
    """
    with tokenize.open(path.as_posix()) as f:
        # Decode the bytes here, because the text layer would turn every line
        # ending into "\n".
        return f.buffer.read().decode(f.encoding)


def failure_reason(*, error: Exception) -> str:
    """Return why reading a file failed, for a message that names the file.

    An OSError from the system names the file again, by its absolute path in
    the system's form, so this gives only its reason. An OSError without one
    gives its own text.
    """
    if isinstance(error, OSError):
        return error.strerror or str(error)
    return str(error)
