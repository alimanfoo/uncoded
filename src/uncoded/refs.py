"""Minimal LSP client that queries ty for textDocument/references."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast
from urllib.parse import unquote, urlparse

from uncoded.body import resolve_name_position
from uncoded.config import find_pyproject_toml

TY_VERSION = "0.0.37"


@dataclass(frozen=True)
class Reference:
    """A reference location with 1-indexed line and column."""

    rel_path: Path
    line: int
    col: int


def find_refs(name_path: str, in_path: Path) -> list[Reference]:
    """Return all references to the symbol named by name_path in in_path.

    Resolves the symbol's name-token position, queries ty's LSP server for
    references, and returns results with 1-indexed line/col sorted by
    (rel_path, line, col). rel_path is relative to the current working
    directory when possible; otherwise absolute.
    Propagates UnsupportedNamePath, SymbolNotFound, FileNotFoundError, and
    SyntaxError from resolve_name_position.
    """
    position = resolve_name_position(name_path, in_path)
    raw_refs = query_references(in_path, position)
    result = [
        Reference(
            rel_path=_to_rel_path(path=ref.path),
            line=ref.line + 1,
            col=ref.character + 1,
        )
        for ref in raw_refs
    ]
    result.sort(key=lambda r: (r.rel_path, r.line, r.col))
    return result


def query_references(in_path: Path, position: tuple[int, int]) -> list[_LSPLocation]:
    """Return raw LSP reference locations for the symbol at position in in_path.

    in_path must be an absolute path; a relative path raises ValueError.
    Spawns ty as a one-shot LSP subprocess and performs the full
    initialize/didOpen/references/shutdown exchange.
    position follows LSP convention: (line, character), both 0-indexed.
    """
    if not in_path.is_absolute():
        raise ValueError(f"query_references requires an absolute path; got {in_path!r}")
    root = _find_root(in_path)
    try:
        proc = subprocess.Popen(
            ["uvx", "--from", f"ty=={TY_VERSION}", "ty", "server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "uvx not found on PATH — install uv (https://docs.astral.sh/uv/)"
        ) from exc
    try:
        return _run_exchange(
            stdin=cast(IO[bytes], proc.stdin),
            stdout=cast(IO[bytes], proc.stdout),
            in_path=in_path,
            position=position,
            root=root,
        )
    finally:
        _terminate(proc=proc)


@dataclass(frozen=True)
class _LSPLocation:
    """Raw LSP reference location with 0-indexed line and character."""

    path: Path
    line: int
    character: int


def _find_root(in_path: Path) -> Path:
    pyproject = find_pyproject_toml(in_path.parent)
    return pyproject.parent if pyproject is not None else in_path.parent


def _terminate(*, proc: subprocess.Popen[bytes]) -> None:
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()


def _to_rel_path(*, path: Path) -> Path:
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def _run_exchange(
    *,
    stdin: IO[bytes],
    stdout: IO[bytes],
    in_path: Path,
    position: tuple[int, int],
    root: Path,
) -> list[_LSPLocation]:
    root_uri = root.as_uri()
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
                "workspaceFolders": [{"uri": root_uri, "name": root.name}],
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
                    "text": in_path.read_text(),
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
                "context": {"includeDeclaration": False},
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

    if "error" in response:
        error = response["error"]
        raise RuntimeError(f"ty LSP error: {error.get('message', error)}")

    result = response["result"]
    if result is None:
        return []
    return [
        _LSPLocation(
            path=_uri_to_path(loc["uri"]),
            line=loc["range"]["start"]["line"],
            character=loc["range"]["start"]["character"],
        )
        for loc in result
    ]


def _write_message(*, stream: IO[bytes], msg: dict) -> None:
    data = json.dumps(msg).encode("utf-8")
    stream.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data)
    stream.flush()


def _read_message(*, stream: IO[bytes]) -> dict:
    headers = b""
    while not headers.endswith(b"\r\n\r\n"):
        ch = stream.read(1)
        if not ch:
            raise RuntimeError("ty closed stdout unexpectedly")
        headers += ch
    length = int(headers.split(b"\r\n")[0].split(b":", 1)[1].strip())
    return json.loads(stream.read(length).decode("utf-8"))


def _read_response(*, stream: IO[bytes], request_id: int) -> dict:
    while True:
        msg = _read_message(stream=stream)
        if msg.get("id") == request_id:
            return msg


def _uri_to_path(uri: str) -> Path:
    return Path(unquote(urlparse(uri).path))
