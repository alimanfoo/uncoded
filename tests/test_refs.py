import io
import json
import subprocess
import textwrap
from pathlib import Path
from unittest import mock

import pytest

from uncoded.refs import (
    Reference,
    _find_root,
    _LSPLocation,
    _read_message,
    _read_response,
    _run_exchange,
    _terminate,
    _to_rel_path,
    find_refs,
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


class TestFindRefs:
    def test_returns_empty_for_dead_symbol(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def uncalled():\n    pass\n")

        refs = find_refs("uncalled", pkg / "a.py")

        assert refs == []

    def test_finds_multiple_references_across_files(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n"
        )

        refs = find_refs("foo", pkg / "a.py")

        assert len(refs) == 2
        assert all(isinstance(r, Reference) for r in refs)
        assert all(r.rel_path == pkg / "b.py" for r in refs)
        assert [r.line for r in refs] == [2, 3]
        assert all(r.col >= 1 for r in refs)

    def test_class_method_shape(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text(
            textwrap.dedent("""\
            class Dog:
                def bark(self):
                    pass
        """)
        )
        (pkg / "b.py").write_text(
            "from pkg.a import Dog\nd = Dog()\nd.bark()\nd.bark()\n"
        )

        refs = find_refs("Dog/bark", pkg / "a.py")

        assert len(refs) == 2
        assert all(r.rel_path == pkg / "b.py" for r in refs)

    def test_results_are_sorted(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n"
        )

        refs = find_refs("foo", pkg / "a.py")

        assert refs == sorted(refs, key=lambda r: (r.rel_path, r.line, r.col))

    def test_line_and_col_are_one_indexed(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text("from pkg.a import foo\nfoo()\n")

        refs = find_refs("foo", pkg / "a.py")

        assert len(refs) == 1
        assert refs[0].line == 2
        assert refs[0].col == 1

    def test_path_with_spaces_is_not_percent_encoded(self, tmp_path):
        root = tmp_path / "my project"
        root.mkdir()
        (root / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (root / "a.py").write_text("def foo():\n    pass\n")
        (root / "b.py").write_text("from a import foo\nfoo()\n")

        refs = find_refs("foo", root / "a.py")

        assert len(refs) == 1
        assert "%20" not in str(refs[0].rel_path)
        assert " " in str(refs[0].rel_path)


class TestToRelPath:
    def test_returns_relative_path_when_under_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "pkg" / "m.py"

        result = _to_rel_path(path=path)

        assert result == Path("pkg/m.py")

    def test_returns_absolute_path_when_outside_cwd(self, tmp_path, monkeypatch):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        other = tmp_path / "elsewhere" / "m.py"

        result = _to_rel_path(path=other)

        assert result == other


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
        assert all(isinstance(r, _LSPLocation) for r in refs)
        assert all(r.path == pkg / "b.py" for r in refs)
        assert {r.line for r in refs} == {1, 2}

    def test_uvx_not_found_raises_runtime_error(self, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n")

        with (
            mock.patch("uncoded.refs.subprocess.Popen", side_effect=FileNotFoundError),
            pytest.raises(RuntimeError, match="uvx not found"),
        ):
            query_references(in_path, (0, 4))

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
            },
            _shutdown_response(),
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
