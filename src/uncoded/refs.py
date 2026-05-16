"""Minimal LSP client that queries ty for textDocument/references."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast
from urllib.parse import urlparse

from uncoded.config import find_pyproject_toml

TY_VERSION = "0.0.37"


@dataclass(frozen=True)
class Reference:
    """A single reference location returned by ty's LSP server."""

    path: Path
    line: int
    character: int


def query_references(in_path: Path, position: tuple[int, int]) -> list[Reference]:
    """Return all references to the symbol at position in in_path.

    Spawns ty as a one-shot LSP subprocess and performs the full
    initialize/didOpen/references/shutdown exchange.
    position follows LSP convention: (line, character), both 0-indexed.
    """
    root = _find_root(in_path)
    proc = subprocess.Popen(
        ["uvx", "--from", f"ty=={TY_VERSION}", "ty", "server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
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


def _find_root(in_path: Path) -> Path:
    pyproject = find_pyproject_toml(in_path.parent)
    return pyproject.parent if pyproject is not None else in_path.parent


def _terminate(*, proc: subprocess.Popen[bytes]) -> None:
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()


def _run_exchange(
    *,
    stdin: IO[bytes],
    stdout: IO[bytes],
    in_path: Path,
    position: tuple[int, int],
    root: Path,
) -> list[Reference]:
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

    if "error" in response:
        raise RuntimeError(f"ty LSP error: {response['error']}")

    _write_message(
        stream=stdin,
        msg={"jsonrpc": "2.0", "id": 3, "method": "shutdown", "params": None},
    )
    _read_response(stream=stdout, request_id=3)
    _write_message(stream=stdin, msg={"jsonrpc": "2.0", "method": "exit"})

    result = response["result"]
    if result is None:
        return []
    return [
        Reference(
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
    return Path(urlparse(uri).path)
