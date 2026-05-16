import io
import json
import subprocess
from unittest import mock

import pytest

from uncoded.refs import (
    Reference,
    _find_root,
    _read_message,
    _read_response,
    _run_exchange,
    _terminate,
    query_references,
)


def _lsp_stream(*msgs: dict) -> io.BytesIO:
    """Build a BytesIO stream pre-loaded with LSP-framed messages."""
    data = b""
    for msg in msgs:
        body = json.dumps(msg).encode("utf-8")
        data += f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
    return io.BytesIO(data)


def _init_response() -> dict:
    return {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}


def _shutdown_response() -> dict:
    return {"jsonrpc": "2.0", "id": 3, "result": None}


class TestQueryReferences:
    def test_finds_call_sites(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n"
        )

        refs = query_references(pkg / "a.py", (0, 4))

        assert len(refs) == 2
        assert all(isinstance(r, Reference) for r in refs)
        assert all(r.path == pkg / "b.py" for r in refs)
        assert {r.line for r in refs} == {1, 2}

    def test_returns_empty_list_when_no_references(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        m = tmp_path / "m.py"
        m.write_text("# just a comment\ndef foo(): pass\n")

        refs = query_references(m, (0, 2))

        assert refs == []


class TestRunExchange:
    def test_lsp_error_raises(self, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n")

        stdout = _lsp_stream(
            _init_response(),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "error": {"code": -32602, "message": "not open"},
            },  # noqa: E501
        )

        with pytest.raises(RuntimeError, match="ty LSP error"):
            _run_exchange(
                stdin=io.BytesIO(),
                stdout=stdout,
                in_path=in_path,
                position=(0, 4),
                root=tmp_path,
            )

    def test_empty_result_list_returns_empty(self, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n")

        stdout = _lsp_stream(
            _init_response(),
            {"jsonrpc": "2.0", "id": 2, "result": []},
            _shutdown_response(),
        )

        refs = _run_exchange(
            stdin=io.BytesIO(),
            stdout=stdout,
            in_path=in_path,
            position=(0, 4),
            root=tmp_path,
        )

        assert refs == []


class TestFindRoot:
    def test_returns_pyproject_parent_when_found(self, tmp_path):
        sub = tmp_path / "pkg"
        sub.mkdir()
        (tmp_path / "pyproject.toml").write_text("")

        assert _find_root(sub / "m.py") == tmp_path

    def test_returns_in_path_parent_when_not_found(self, tmp_path):
        sub = tmp_path / "pkg"
        sub.mkdir()

        assert _find_root(sub / "m.py") == sub


class TestTerminate:
    def test_kills_on_timeout(self):
        proc = mock.Mock(spec=subprocess.Popen)
        proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]

        _terminate(proc=proc)

        proc.terminate.assert_called_once()
        assert proc.wait.call_count == 2


class TestReadMessage:
    def test_raises_on_closed_stream(self):
        with pytest.raises(RuntimeError, match="closed"):
            _read_message(stream=io.BytesIO(b""))

    def test_parses_framed_message(self):
        msg = {"jsonrpc": "2.0", "id": 1, "result": {}}
        body = json.dumps(msg).encode("utf-8")
        data = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body

        assert _read_message(stream=io.BytesIO(data)) == msg


class TestReadResponse:
    def test_skips_notifications_until_matching_id(self):
        notification = {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {},
        }
        response = {"jsonrpc": "2.0", "id": 7, "result": []}
        stream = _lsp_stream(notification, response)

        assert _read_response(stream=stream, request_id=7) == response
