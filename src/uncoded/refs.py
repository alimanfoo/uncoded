"""Minimal LSP client that queries ty for textDocument/references."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast
from urllib.parse import urlparse
from urllib.request import url2pathname

from uncoded.read_helpers import read_source_text
from uncoded.resolver import NamePath, resolve_name_position

# The ty that `uncoded refs` runs through uvx, kept apart from the dev dependency
# on ty. It is pinned exactly because any ty release can change what
# `uncoded refs` reports. Before you raise it, compare `uncoded refs` output on
# this repository under the old and the new version.
_TY_VERSION = "0.0.92"

_TY_STOPPED = "ty failed: it stopped before it answered."


class TyError(Exception):
    """ty could not be started, or it failed before it answered."""


@dataclass(frozen=True)
class _Reference:
    """A reference location with 1-indexed line and column."""

    path: Path
    line: int
    col: int


def find_refs(
    *, name_path: NamePath, in_path: Path, project_directory: Path
) -> list[_Reference]:
    """Return every reference to the symbol named by name_path in in_path.

    Resolves the symbol's name-token position, queries ty's LSP server for
    references, with project_directory as its workspace, and returns results with
    1-indexed line/col sorted by (path, line, col). path is relative to the
    current working directory when possible; otherwise absolute.
    Raises TyError when ty cannot be started or fails before it answers.
    Propagates SymbolNotFoundError from resolve_name_position. OSError,
    UnicodeDecodeError, and SyntaxError propagate from resolve_name_position
    and from read_source_text in the LSP exchange.
    """
    position = resolve_name_position(name_path=name_path, in_path=in_path)
    raw_refs = _query_references(
        in_path=in_path, position=position, project_directory=project_directory
    )
    result = [
        _Reference(
            path=_path_for_display(path=ref.path),
            line=ref.line + 1,
            col=ref.character + 1,
        )
        for ref in raw_refs
    ]
    result.sort(key=lambda r: (r.path, r.line, r.col))
    return result


def _query_references(
    *, in_path: Path, position: tuple[int, int], project_directory: Path
) -> list[_LSPLocation]:
    """Return raw LSP reference locations for the symbol at position in in_path.

    Spawns ty as a one-shot LSP subprocess and performs the full
    initialize/didOpen/references/shutdown exchange.
    position follows LSP convention: (line, character), both 0-indexed.
    When ty fails, the TyError carries what ty and uvx wrote to standard error.
    """
    # A file rather than a pipe takes ty's error output, because a pipe that
    # nothing reads during the exchange would fill and block ty.
    with tempfile.TemporaryFile() as ty_stderr:
        try:
            return _run_ty(
                in_path=in_path,
                position=position,
                project_directory=project_directory,
                stderr=ty_stderr,
            )
        except TyError as exc:
            ty_stderr.seek(0)
            # splitlines drops the carriage returns of Windows line endings.
            text = ty_stderr.read().decode("utf-8", errors="replace").strip()
            output = "\n".join(text.splitlines())
            if not output:
                raise
            raise TyError(
                f"{exc}\nOutput from uvx and ty:\n{textwrap.indent(output, '  ')}"
            ) from exc


def _run_ty(
    *,
    in_path: Path,
    position: tuple[int, int],
    project_directory: Path,
    stderr: IO[bytes],
) -> list[_LSPLocation]:
    try:
        proc = subprocess.Popen(
            ["uvx", "--from", f"ty=={_TY_VERSION}", "ty", "server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
        )
    except FileNotFoundError as exc:
        raise TyError(
            "uvx not found on PATH — install uv (https://docs.astral.sh/uv/)"
        ) from exc
    except OSError as exc:
        raise TyError(f"uvx could not start: {exc}") from exc
    try:
        return _run_exchange(
            stdin=cast("IO[bytes]", proc.stdin),
            stdout=cast("IO[bytes]", proc.stdout),
            in_path=in_path,
            position=position,
            project_directory=project_directory,
        )
    finally:
        _terminate(proc=proc)


@dataclass(frozen=True)
class _LSPLocation:
    """Raw LSP reference location with 0-indexed line and character."""

    path: Path
    line: int
    character: int


def _terminate(*, proc: subprocess.Popen[bytes]) -> None:
    # Closing ty's input flushes any message that ty never read, and the flush
    # fails once ty has stopped.
    with contextlib.suppress(OSError):
        cast("IO[bytes]", proc.stdin).close()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()


def _path_for_display(*, path: Path) -> Path:
    # ty reports resolved paths, so the current directory is resolved too, in
    # case it is reached through a symbolic link.
    try:
        return path.relative_to(Path.cwd().resolve())
    except ValueError:
        return path


def _run_exchange(
    *,
    stdin: IO[bytes],
    stdout: IO[bytes],
    in_path: Path,
    position: tuple[int, int],
    project_directory: Path,
) -> list[_LSPLocation]:
    in_path = in_path.resolve()
    project_directory = project_directory.resolve()
    root_uri = project_directory.as_uri()
    file_uri = in_path.as_uri()

    _write_message(
        stream=stdin,
        msg={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "workspaceFolders": [{"uri": root_uri, "name": project_directory.name}],
                "capabilities": {},
            },
        },
    )
    _read_response(stream=stdout, request_id=1)

    _write_message(
        stream=stdin,
        msg={"jsonrpc": "2.0", "method": "initialized", "params": {}},
    )

    _write_message(
        stream=stdin,
        msg={
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": file_uri,
                    "languageId": "python",
                    "version": 1,
                    "text": read_source_text(path=in_path),
                }
            },
        },
    )

    line, character = position
    _write_message(
        stream=stdin,
        msg={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/references",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": True},
            },
        },
    )
    response = _read_response(stream=stdout, request_id=2)

    _write_message(
        stream=stdin,
        msg={"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": None},
    )
    _read_response(stream=stdout, request_id=3)
    _write_message(stream=stdin, msg={"jsonrpc": "2.0", "method": "exit"})

    return [
        _LSPLocation(
            path=_uri_to_path(uri=loc["uri"]),
            line=loc["range"]["start"]["line"],
            character=loc["range"]["start"]["character"],
        )
        for loc in response["result"] or []
    ]


def _write_message(*, stream: IO[bytes], msg: dict) -> None:
    data = json.dumps(msg).encode("utf-8")
    try:
        stream.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data)
        stream.flush()
    except OSError as exc:
        raise TyError(_TY_STOPPED) from exc


def _read_message(*, stream: IO[bytes]) -> dict:
    headers = b""
    while not headers.endswith(b"\r\n\r\n"):
        ch = stream.read(1)
        if not ch:
            raise TyError(_TY_STOPPED)
        headers += ch
    try:
        length = int(headers.split(b"\r\n")[0].split(b":", 1)[1].strip())
        return json.loads(stream.read(length).decode("utf-8"))
    except (IndexError, ValueError) as exc:
        raise TyError("ty failed: it sent a message that is not valid LSP.") from exc


def _read_response(*, stream: IO[bytes], request_id: int) -> dict:
    while True:
        msg = _read_message(stream=stream)
        if msg.get("id") != request_id:
            continue
        if "error" in msg:
            error = msg["error"]
            raise TyError(
                f"ty failed: it answered with an error: {error.get('message', error)}"
            )
        return msg


def _uri_to_path(*, uri: str) -> Path:
    # url2pathname decodes the percent escapes and, on Windows, turns a URI path
    # such as /C:/src/m.py into C:\src\m.py.
    return Path(url2pathname(urlparse(uri).path))
