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


def root_files(
    *, roots: list[Path], pattern: str, project_directory: Path
) -> list[tuple[Path, str]]:
    """List each matching file under ``roots`` with its project-relative path.

    A file root lists itself. A directory root lists files that match the
    pattern. Files under overlapping roots are listed once, in path order. Each
    relative path uses forward slashes on every platform.
    """
    project_directory = project_directory.resolve()
    paths: dict[str, Path] = {}
    for root in roots:
        resolved_root = root.resolve()
        files = (
            [resolved_root] if resolved_root.is_file() else resolved_root.rglob(pattern)
        )
        for path in files:
            rel_path = path.relative_to(project_directory).as_posix()
            paths[rel_path] = path
    return [(path, rel_path) for rel_path, path in sorted(paths.items())]


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
    the system's form, so this gives only its reason. A SyntaxError can do the
    same for a malformed encoding cookie. An error without a filename gives
    its own text.
    """
    if isinstance(error, OSError):
        return error.strerror or str(error)
    if isinstance(error, SyntaxError):
        message = error.msg
        prefix, separator, reason = message.rpartition(": ")
        error_kind, marker, _filename = prefix.partition(" for ")
        if marker and separator:
            message = f"{error_kind}: {reason}"
        line = f" at line {error.lineno}" if error.lineno is not None else ""
        return f"SyntaxError{line}: {message}"
    return str(error)
