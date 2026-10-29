import io
import json
import os
import subprocess
import textwrap
from pathlib import Path
from unittest import mock

import pytest

from uncoded.refs import (
    _TY_VERSION,
    TyError,
    _LSPLocation,
    _path_for_display,
    _query_references,
    _read_message,
    _read_response,
    _Reference,
    _run_exchange,
    _terminate,
    _uri_to_path,
    find_refs,
)
from uncoded.resolver import NamePath


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


class TestFindRefsWithoutTy:
    def test_converts_and_sorts_locations(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")
        locations = [
            _LSPLocation(path=tmp_path / "b.py", line=4, character=8),
            _LSPLocation(path=tmp_path / "a.py", line=1, character=4),
        ]

        with mock.patch("uncoded.refs._query_references", return_value=locations):
            refs = find_refs(
                name_path=NamePath("foo"),
                in_path=in_path,
                project_directory=tmp_path,
            )

        assert refs == [
            _Reference(path=tmp_path / "a.py", line=2, col=5),
            _Reference(path=tmp_path / "b.py", line=5, col=9),
        ]


@pytest.mark.integration
class TestFindRefs:
    @pytest.mark.parametrize(
        ("source", "name", "positions"),
        [
            pytest.param(
                "def  foo():\n    pass\n\n\nfoo()\n",
                "foo",
                [(1, 6), (5, 1)],
                id="function-with-two-spaces",
            ),
            pytest.param(
                "class\tEngine:\n    pass\n\nEngine()\n",
                "Engine",
                [(1, 7), (4, 1)],
                id="class-with-tab",
            ),
            pytest.param(
                "async def   fetch():\n    pass\n\nfetch()\n",
                "fetch",
                [(1, 13), (4, 1)],
                id="async-function-with-extra-spaces",
            ),
            pytest.param(
                "def \\\n    continued():\n    pass\n\ncontinued()\n",
                "continued",
                [(2, 5), (5, 1)],
                id="line-continuation",
            ),
            pytest.param(
                (
                    "import functools\n\n"
                    "@functools.cache\n"
                    "def decorated():\n"
                    "    pass\n\n"
                    "decorated()\n"
                ),
                "decorated",
                [(4, 5), (7, 1)],
                id="decorated-function",
            ),
        ],
    )
    def test_definition_name_follows_token(self, *, tmp_path, source, name, positions):
        path = tmp_path / "a.py"
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        path.write_text(source, encoding="utf-8")

        refs = find_refs(
            name_path=NamePath(name),
            in_path=path,
            project_directory=tmp_path,
        )

        assert refs == [
            _Reference(path=path, line=line, col=col) for line, col in positions
        ]

    def test_unused_symbol_has_only_its_definition(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text("def uncalled():\n    pass\n", encoding="utf-8")

        refs = find_refs(
            name_path=NamePath("uncalled"),
            in_path=pkg / "a.py",
            project_directory=tmp_path,
        )

        assert refs == [_Reference(path=pkg / "a.py", line=1, col=5)]

    def test_finds_definition_imports_and_uses_across_files(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text("def foo():\n    return 42\n", encoding="utf-8")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n", encoding="utf-8"
        )
        (pkg / "c.py").write_text("from pkg.a import foo as bar\n", encoding="utf-8")

        refs = find_refs(
            name_path=NamePath("foo"), in_path=pkg / "a.py", project_directory=tmp_path
        )

        assert refs == [
            _Reference(path=pkg / "a.py", line=1, col=5),
            _Reference(path=pkg / "b.py", line=1, col=19),
            _Reference(path=pkg / "b.py", line=2, col=10),
            _Reference(path=pkg / "b.py", line=3, col=9),
            _Reference(path=pkg / "c.py", line=1, col=19),
        ]

    def test_finds_each_reference_to_a_method(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text(
            textwrap.dedent("""\
            class Dog:
                def bark(self):
                    pass
        """),
            encoding="utf-8",
        )
        (pkg / "b.py").write_text(
            "from pkg.a import Dog\nd = Dog()\nd.bark()\nd.bark()\n", encoding="utf-8"
        )

        refs = find_refs(
            name_path=NamePath("Dog", "bark"),
            in_path=pkg / "a.py",
            project_directory=tmp_path,
        )

        assert refs == [
            _Reference(path=pkg / "a.py", line=2, col=9),
            _Reference(path=pkg / "b.py", line=3, col=3),
            _Reference(path=pkg / "b.py", line=4, col=3),
        ]

    def test_results_are_sorted(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text("def foo():\n    return 42\n", encoding="utf-8")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n", encoding="utf-8"
        )

        refs = find_refs(
            name_path=NamePath("foo"), in_path=pkg / "a.py", project_directory=tmp_path
        )

        assert refs == sorted(refs, key=lambda r: (r.path, r.line, r.col))

    def test_line_and_col_are_one_indexed(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text("def foo():\n    return 42\n", encoding="utf-8")
        (pkg / "b.py").write_text("from pkg.a import foo\nfoo()\n", encoding="utf-8")

        refs = find_refs(
            name_path=NamePath("foo"), in_path=pkg / "a.py", project_directory=tmp_path
        )

        assert refs[-1] == _Reference(path=pkg / "b.py", line=2, col=1)

    def test_path_with_spaces_is_not_percent_encoded(self, *, tmp_path):
        project_directory = tmp_path / "my project"
        project_directory.mkdir()
        (project_directory / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (project_directory / "a.py").write_text(
            "def foo():\n    pass\n", encoding="utf-8"
        )
        (project_directory / "b.py").write_text(
            "from a import foo\nfoo()\n", encoding="utf-8"
        )

        refs = find_refs(
            name_path=NamePath("foo"),
            in_path=project_directory / "a.py",
            project_directory=project_directory,
        )

        assert refs[0].path == project_directory / "a.py"
        assert all("%20" not in str(r.path) for r in refs)


class TestPathForDisplay:
    def test_returns_relative_path_when_under_cwd(self, *, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = tmp_path / "pkg" / "m.py"

        result = _path_for_display(path=path)

        assert result == Path("pkg/m.py")

    def test_returns_relative_path_when_cwd_is_a_symbolic_link(
        self, *, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        link = tmp_path / "link"
        link.symlink_to(project, target_is_directory=True)
        monkeypatch.chdir(link)

        result = _path_for_display(path=project.resolve() / "pkg" / "m.py")

        assert result == Path("pkg/m.py")

    def test_returns_absolute_path_when_outside_cwd(self, *, tmp_path, monkeypatch):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        monkeypatch.chdir(workspace)
        other = tmp_path / "elsewhere" / "m.py"

        result = _path_for_display(path=other)

        assert result == other


class TestUriToPath:
    def test_keeps_host_in_network_path(self):
        result = _uri_to_path(uri="file://server/share/pkg/m.py")

        assert result.as_posix().lstrip("/") == "server/share/pkg/m.py"

    @pytest.mark.skipif(
        os.name != "nt", reason="UNC paths have their native form only on Windows."
    )
    def test_returns_unc_path_for_uri_with_host(self):
        result = _uri_to_path(uri="file://server/share/pkg/m.py")

        assert result == Path(r"\\server\share\pkg\m.py")

    def test_uses_uri_path_without_host(self):
        result = _uri_to_path(uri="file:///share/pkg/m.py")

        assert result.as_posix() == "/share/pkg/m.py"


class TestQueryReferences:
    @pytest.mark.integration
    def test_finds_definition_import_and_call_sites(self, *, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        (pkg / "a.py").write_text("def foo():\n    return 42\n", encoding="utf-8")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n", encoding="utf-8"
        )

        refs = _query_references(
            in_path=pkg / "a.py", position=(0, 4), project_directory=tmp_path
        )

        assert sorted(refs, key=lambda r: (r.path, r.line, r.character)) == [
            _LSPLocation(path=pkg / "a.py", line=0, character=4),
            _LSPLocation(path=pkg / "b.py", line=0, character=18),
            _LSPLocation(path=pkg / "b.py", line=1, character=9),
            _LSPLocation(path=pkg / "b.py", line=2, character=8),
        ]

    def test_reports_missing_uvx(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")

        with (
            mock.patch("uncoded.refs.subprocess.Popen", side_effect=FileNotFoundError),
            pytest.raises(TyError, match="uvx not found"),
        ):
            _query_references(
                in_path=in_path, position=(0, 4), project_directory=tmp_path
            )

    def test_reports_uvx_start_failure(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")

        with (
            mock.patch(
                "uncoded.refs.subprocess.Popen",
                side_effect=PermissionError(13, "Permission denied"),
            ),
            pytest.raises(
                TyError,
                match=r"^uvx could not start: .*Permission denied$",
            ),
        ):
            _query_references(
                in_path=in_path, position=(0, 4), project_directory=tmp_path
            )

    @pytest.mark.integration
    def test_returns_empty_list_when_no_references(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "t"\n', encoding="utf-8"
        )
        m = tmp_path / "m.py"
        m.write_text("# just a comment\ndef foo(): pass\n", encoding="utf-8")

        refs = _query_references(in_path=m, position=(0, 2), project_directory=tmp_path)

        assert refs == []

    def test_starts_the_pinned_ty_and_returns_its_locations(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")
        ref_path = tmp_path / "other.py"
        references_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": [
                {
                    "uri": ref_path.as_uri(),
                    "range": {"start": {"line": 3, "character": 7}},
                }
            ],
        }
        mock_proc = mock.Mock(spec=subprocess.Popen)
        mock_proc.stdin = io.BytesIO()
        mock_proc.stdout = _lsp_stream(
            _init_response(), references_response, _shutdown_response()
        )

        with mock.patch(
            "uncoded.refs.subprocess.Popen", return_value=mock_proc
        ) as mock_popen:
            refs = _query_references(
                in_path=in_path, position=(0, 4), project_directory=tmp_path
            )

        assert refs == [_LSPLocation(path=ref_path, line=3, character=7)]
        mock_popen.assert_called_once_with(
            ["uvx", "--from", f"ty=={_TY_VERSION}", "ty", "server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=mock.ANY,
        )
        mock_proc.wait.assert_called()


class TestRunExchange:
    def test_raises_when_ty_answers_with_an_error(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")

        stdout = _lsp_stream(
            _init_response(),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "error": {"code": -32602, "message": "not open"},
            },
            _shutdown_response(),
        )

        with pytest.raises(
            TyError, match=r"^ty failed: it answered with an error: not open$"
        ):
            _run_exchange(
                stdin=io.BytesIO(),
                stdout=stdout,
                in_path=in_path,
                position=(0, 4),
                project_directory=tmp_path,
            )

    def test_treats_an_empty_reference_list_as_no_references(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")

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
            project_directory=tmp_path,
        )

        assert refs == []

    def test_treats_a_null_reference_list_as_no_references(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")

        stdout = _lsp_stream(
            _init_response(),
            {"jsonrpc": "2.0", "id": 2, "result": None},
            _shutdown_response(),
        )

        refs = _run_exchange(
            stdin=io.BytesIO(),
            stdout=stdout,
            in_path=in_path,
            position=(0, 4),
            project_directory=tmp_path,
        )

        assert refs == []


class TestTyFailures:
    """uncoded refs with a stand-in for ty that fails."""

    def _query(self, *, tmp_path):
        in_path = tmp_path / "m.py"
        in_path.write_text("def foo(): pass\n", encoding="utf-8")
        return _query_references(
            in_path=in_path, position=(0, 4), project_directory=tmp_path
        )

    def test_ty_that_exits_at_once(self, *, tmp_path, stand_in_for_ty):
        stand_in_for_ty(script="sys.exit(1)")

        with pytest.raises(
            TyError, match=r"^ty failed: it stopped before it answered\.$"
        ):
            self._query(tmp_path=tmp_path)

    def test_passes_on_what_uvx_and_ty_wrote(self, *, tmp_path, stand_in_for_ty):
        stand_in_for_ty(
            script="""
            sys.stderr.buffer.write(b"Resolved 1 package\\r\\n")
            sys.stderr.write("error: Failed to fetch: https://pypi.org/simple/ty/\\n")
            sys.exit(2)
            """
        )

        with pytest.raises(TyError) as exc_info:
            self._query(tmp_path=tmp_path)

        assert str(exc_info.value) == (
            "ty failed: it stopped before it answered.\n"
            "Output from uvx and ty:\n"
            "  Resolved 1 package\n"
            "  error: Failed to fetch: https://pypi.org/simple/ty/"
        )

    # Closing ty's input when the exchange ends must not leave a failed flush
    # for the garbage collector to report.
    @pytest.mark.filterwarnings("error::pytest.PytestUnraisableExceptionWarning")
    def test_ty_that_stops_reading(self, *, tmp_path, stand_in_for_ty):
        stand_in_for_ty(
            script="""
            read_message()
            os.close(0)
            send(INITIALIZE_RESPONSE)
            """
        )

        with pytest.raises(
            TyError, match=r"^ty failed: it stopped before it answered\.$"
        ):
            self._query(tmp_path=tmp_path)

    def test_ty_that_sends_invalid_message(self, *, tmp_path, stand_in_for_ty):
        stand_in_for_ty(
            script="""
            read_message()
            send(b"\\xff")
            """
        )

        with pytest.raises(
            TyError, match=r"^ty failed: it sent a message that is not valid LSP\.$"
        ):
            self._query(tmp_path=tmp_path)


class TestTerminate:
    def test_terminates_ty_that_does_not_stop_in_time(self):
        proc = mock.Mock(spec=subprocess.Popen)
        proc.stdin = io.BytesIO()
        proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 5), None]

        _terminate(proc=proc)

        proc.terminate.assert_called_once()
        assert proc.wait.call_count == 2


class TestReadMessage:
    def test_raises_on_closed_stream(self):
        with pytest.raises(TyError, match="stopped before it answered"):
            _read_message(stream=io.BytesIO(b""))

    @pytest.mark.parametrize(
        "data",
        [
            pytest.param(b"Content-Length 2\r\n\r\n{}", id="header-without-colon"),
            pytest.param(b"Content-Length: x\r\n\r\n{}", id="length-not-a-number"),
            pytest.param(b"Content-Length: 1\r\n\r\n\xff", id="body-not-utf-8"),
            pytest.param(b"Content-Length: 1\r\n\r\n{", id="body-not-json"),
        ],
    )
    def test_raises_on_invalid_message(self, *, data):
        with pytest.raises(TyError, match="not valid LSP"):
            _read_message(stream=io.BytesIO(data))

    def test_parses_framed_message(self):
        msg = {"jsonrpc": "2.0", "id": 1, "result": {}}
        body = json.dumps(msg).encode("utf-8")
        data = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body

        assert _read_message(stream=io.BytesIO(data)) == msg


class TestReadResponse:
    def test_skips_non_responses_until_matching_id(self):
        notification = {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {},
        }
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "workspace/configuration",
            "params": {},
        }
        response = {"jsonrpc": "2.0", "id": 7, "result": []}
        stream = _lsp_stream(notification, request, response)

        assert _read_response(stream=stream, request_id=7) == response

    def test_raises_on_error_reply(self):
        stream = _lsp_stream(
            {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": "boom"}}
        )

        with pytest.raises(
            TyError, match=r"^ty failed: it answered with an error: boom$"
        ):
            _read_response(stream=stream, request_id=1)
