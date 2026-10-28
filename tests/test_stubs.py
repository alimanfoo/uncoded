import textwrap
from pathlib import Path

import pytest

from uncoded.extract import (
    AssignmentSymbol,
    ClassSymbol,
    FunctionSymbol,
    Parameter,
    PythonFile,
    TypeAliasSymbol,
    _extract_python_file,
    extract_python_files,
    read_source_files,
)
from uncoded.markers import GENERATED_MARKER
from uncoded.stubs import _render_stub, sync_stubs


def _setup(*, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "stubs"
    return src, out


def _sync_root(*, source_root, out, tmp_path, check=False):
    files, _skipped = read_source_files(
        source_root=source_root, project_directory=tmp_path
    )
    return sync_stubs(
        python_files=extract_python_files(files=files),
        output_dir=out,
        project_directory=tmp_path,
        check=check,
    )


class TestRenderStub:
    def test_header_contains_path(self):
        module = PythonFile(rel_path="src/pkg/mod.py")
        lines = _render_stub(python_file=module).splitlines()
        assert lines[0] == f"# {GENERATED_MARKER}"
        assert lines[1] == "# src/pkg/mod.py"

    def test_imports_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            imports=["import os", "from pathlib import Path"],
        )
        output = _render_stub(python_file=module)
        assert "import os\nfrom pathlib import Path\n" in output

    def test_rendered_stub_has_no_line_range_comments(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[
                AssignmentSymbol(name="VALUE", value="1"),
                FunctionSymbol(name="run"),
                ClassSymbol(
                    name="Worker",
                    methods=[
                        FunctionSymbol(
                            name="work",
                            params=[Parameter("self")],
                        )
                    ],
                ),
            ],
        )
        output = _render_stub(python_file=module)
        assert "VALUE = 1\n" in output
        assert "def run():\n    ...\n" in output
        assert "class Worker:\n    def work(self):\n        ...\n" in output
        assert "# L" not in output

    def test_async_function_prefix(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[FunctionSymbol(name="fetch", is_async=True)],
        )
        assert "async def fetch():\n    ...\n" in _render_stub(python_file=module)

    @pytest.mark.parametrize(
        ("params", "expected"),
        [
            pytest.param(
                [Parameter("x")],
                "def f(x):",
                id="regular_positional_bare",
            ),
            pytest.param(
                [Parameter("x", "str")],
                "def f(x: str):",
                id="regular_positional_annotated",
            ),
            pytest.param(
                [Parameter("*args")],
                "def f(*args):",
                id="varargs_bare",
            ),
            pytest.param(
                [Parameter("*args", "str")],
                "def f(*args: str):",
                id="varargs_annotated",
            ),
            pytest.param(
                [Parameter("**kwargs")],
                "def f(**kwargs):",
                id="kwargs_bare",
            ),
            pytest.param(
                [Parameter("**kwargs", "int")],
                "def f(**kwargs: int):",
                id="kwargs_annotated",
            ),
            pytest.param(
                [Parameter("/")],
                "def f(/):",
                id="positional_only_separator",
            ),
            pytest.param(
                [Parameter("*")],
                "def f(*):",
                id="keyword_only_separator",
            ),
        ],
    )
    def test_renders_each_kind_of_parameter(self, *, params, expected):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[FunctionSymbol(name="f", params=params)],
        )
        assert expected in _render_stub(python_file=module)

    def test_return_annotation_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[FunctionSymbol(name="f", return_annotation="str")],
        )
        assert "def f() -> str:" in _render_stub(python_file=module)

    def test_class_with_bases(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[ClassSymbol(name="Dog", bases=["Animal"])],
        )
        assert "class Dog(Animal):\n    ...\n" in _render_stub(python_file=module)

    def test_class_with_no_members_renders_body(self):
        # A class with no attributes and no methods needs an explicit
        # body so the rendered stub is valid Python.
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[ClassSymbol(name="Sentinel")],
        )
        output = _render_stub(python_file=module)
        assert "class Sentinel:\n    ...\n" in output
        compile(output, "pkg/mod.pyi", "exec")

    def test_attribute_with_annotation(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[
                ClassSymbol(
                    name="Record",
                    attributes=[AssignmentSymbol("name", annotation="str")],
                )
            ],
        )
        assert "class Record:\n    name: str\n" in _render_stub(python_file=module)

    def test_method_indented(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[
                ClassSymbol(
                    name="Foo",
                    methods=[
                        FunctionSymbol(
                            name="bar",
                            params=[Parameter("self")],
                        )
                    ],
                )
            ],
        )
        output = _render_stub(python_file=module)
        assert "class Foo:\n    def bar(self):\n        ...\n" in output

    def test_ends_with_newline(self):
        module = PythonFile(rel_path="pkg/mod.py")
        assert _render_stub(python_file=module).endswith("\n")

    def test_property_rendered_as_class_attribute(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self) -> Path:
                    return self._path

                @path.setter
                def path(self, value: Path) -> None:
                    self._path = value
        """)
        module = _extract_python_file(source=source, rel_path="pkg/cfg.py")
        output = _render_stub(python_file=module)
        assert "class Config:\n    path: Path\n" in output
        assert "def path" not in output

    def test_assignment_with_value_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[AssignmentSymbol(name="TIMEOUT", value="30")],
        )
        assert "TIMEOUT = 30\n" in _render_stub(python_file=module)

    def test_assignment_annotated_with_value_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[
                AssignmentSymbol(
                    name="MAX",
                    annotation="int",
                    value="3",
                )
            ],
        )
        assert "MAX: int = 3\n" in _render_stub(python_file=module)

    def test_assignment_value_too_long_elided(self):
        long_list = "[" + ", ".join(f'"item{i}"' for i in range(50)) + "]"
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[AssignmentSymbol(name="BIG", value=long_list)],
        )
        assert "BIG = ...\n" in _render_stub(python_file=module)

    def test_assignment_bare_annotation_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[AssignmentSymbol(name="FOO", annotation="int")],
        )
        output = _render_stub(python_file=module)
        assert "FOO: int\n" in output
        assert "FOO: int = " not in output

    def test_type_alias_pep695_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[TypeAliasSymbol(name="UserId", value="int")],
        )
        assert "type UserId = int\n" in _render_stub(python_file=module)

    def test_unannotated_class_attribute_rendered(self):
        module = PythonFile(
            rel_path="pkg/mod.py",
            symbols=[
                ClassSymbol(
                    name="Registry",
                    attributes=[AssignmentSymbol("items", value="[]")],
                )
            ],
        )
        output = _render_stub(python_file=module)
        assert "class Registry:\n    items = []\n" in output
        assert "# L" not in output

    def test_renders_valid_python_for_representative_source(self):
        source = textwrap.dedent("""\
            import os
            from pathlib import Path

            MAX: int = 3
            TIMEOUT = 30
            type Ids = list[int]

            def greet(name: str) -> str:
                return f"hi {name}"

            async def fetch(url: str) -> bytes:
                return b""

            def build(*args: str, **kwargs: int) -> None:
                pass

            def collect(*args, **kwargs):
                pass

            def separators(x, /, *, y):
                pass

            def configure(retries: int = 3) -> None:
                pass

            class Record:
                name: str
                value: int

                @property
                def display(self) -> str:
                    return self.name

                def save(self) -> None:
                    pass

            class Sentinel:
                pass

            class Dog(Animal):
                pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/representative.py")
        output = _render_stub(python_file=module)
        compile(output, "pkg/representative.pyi", "exec")

    def test_leaves_out_decorators_docstrings_and_bodies(self):
        source = textwrap.dedent("""\
            import functools

            @functools.cache
            def area(width: int, height: int = 1) -> int:
                '''Return the area.'''
                return width * height

            class Shape:
                '''A shape.'''

                @staticmethod
                def unit() -> "Shape":
                    '''Return the unit shape.'''
                    return Shape()
        """)

        output = _render_stub(
            python_file=_extract_python_file(source=source, rel_path="pkg/m.py")
        )

        assert output == (
            f"# {GENERATED_MARKER}\n"
            "# pkg/m.py\n"
            "\n"
            "import functools\n"
            "\n"
            "def area(width: int, height: int) -> int:\n"
            "    ...\n"
            "\n"
            "class Shape:\n"
            "    def unit() -> 'Shape':\n"
            "        ...\n"
        )

    def test_shows_each_definition_of_a_name_defined_twice(self):
        source = textwrap.dedent("""\
            def area(width): ...
            def area(width, height): ...
        """)

        output = _render_stub(
            python_file=_extract_python_file(source=source, rel_path="m.py")
        )

        assert output.endswith(
            "def area(width):\n    ...\n\ndef area(width, height):\n    ...\n"
        )


class TestSyncStubs:
    """sync_stubs writes expected stubs and removes every other stub."""

    def test_writes_expected_stubs(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "foo.pyi").exists()

    def test_removes_orphan_stub_when_source_deleted(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        (src / "bar.py").write_text("def goodbye(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "bar.pyi").exists()

        (src / "bar.py").unlink()
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "foo.pyi").exists()
        assert not (out / "src" / "bar.pyi").exists()

    def test_removes_orphan_stub_when_source_renamed(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "old_name.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "old_name.pyi").exists()

        (src / "old_name.py").rename(src / "new_name.py")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "new_name.pyi").exists()
        assert not (out / "src" / "old_name.pyi").exists()

    def test_prunes_empty_directories(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        pkg = src / "pkg"
        pkg.mkdir()
        (pkg / "mod.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "pkg" / "mod.pyi").exists()

        # Remove the whole subpackage; the stub directory should be pruned.
        (pkg / "mod.py").unlink()
        pkg.rmdir()
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert not (out / "src" / "pkg").exists()

    def test_removes_stubs_of_a_source_root_left_out(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        tests = tmp_path / "tests"
        tests.mkdir()
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        (tests / "test_foo.py").write_text("def test_hello(): pass\n", encoding="utf-8")
        src_files, _skipped = read_source_files(
            source_root=src, project_directory=tmp_path
        )
        test_files, _skipped = read_source_files(
            source_root=tests, project_directory=tmp_path
        )

        sync_stubs(
            python_files=extract_python_files(files=src_files + test_files),
            output_dir=out,
            project_directory=tmp_path,
            check=False,
        )
        assert (out / "src" / "foo.pyi").exists()
        assert (out / "tests" / "test_foo.pyi").exists()

        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "foo.pyi").exists()
        assert not (out / "tests").exists()

    def test_keeps_stubs_when_current(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        # Second build with no source changes should not error and should
        # leave the stub in place.
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert (out / "src" / "foo.pyi").exists()

    def test_reports_count_on_first_sync(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        (src / "bar.py").write_text("def goodbye(): pass\n", encoding="utf-8")
        assert _sync_root(source_root=src, out=out, tmp_path=tmp_path) == 2

    def test_reports_zero_when_current(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert _sync_root(source_root=src, out=out, tmp_path=tmp_path) == 0

    def test_skips_module_with_no_symbols(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "empty.py").write_text(
            '"""Only a module docstring."""\n', encoding="utf-8"
        )
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert not (out / "src" / "empty.pyi").exists()
        assert (out / "src" / "foo.pyi").exists()


class TestSyncStubsCheckMode:
    """sync_stubs with check=True must report changes without mutating the tree."""

    def test_does_not_write_stub_in_check_mode(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        changes = _sync_root(source_root=src, out=out, tmp_path=tmp_path, check=True)
        assert changes == 1
        assert not (out / "src" / "foo.pyi").exists()

    def test_zero_changes_when_current(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        assert _sync_root(source_root=src, out=out, tmp_path=tmp_path, check=True) == 0

    def test_detects_stale_stub_content(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        # Simulate a source edit that would change the stub.
        (src / "foo.py").write_text(
            "def hello(name: str) -> str: pass\n", encoding="utf-8"
        )
        assert _sync_root(source_root=src, out=out, tmp_path=tmp_path, check=True) == 1

    def test_detects_orphan_stub_without_removing_it(self, *, tmp_path):
        src, out = _setup(tmp_path=tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n", encoding="utf-8")
        (src / "bar.py").write_text("def goodbye(): pass\n", encoding="utf-8")
        _sync_root(source_root=src, out=out, tmp_path=tmp_path)
        (src / "bar.py").unlink()
        assert _sync_root(source_root=src, out=out, tmp_path=tmp_path, check=True) == 1
        # Check mode must not mutate the tree — orphan is still there.
        assert (out / "src" / "bar.pyi").exists()


class TestSyncStubsProjectDirectoryAnchor:
    def test_project_directory_anchors_writes_independent_of_cwd(
        self, *, tmp_path, monkeypatch
    ):
        # output_dir is project-relative; project_directory anchors the actual
        # writes under tmp_path even when cwd is elsewhere.
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)
        out = Path("stubs")

        changes = sync_stubs(
            python_files=[
                _extract_python_file(
                    source="def hello(): pass\n", rel_path="src/foo.py"
                )
            ],
            output_dir=out,
            project_directory=tmp_path,
            check=False,
        )

        assert changes == 1
        assert (tmp_path / out / "src" / "foo.pyi").exists()
        assert not (sub / out / "src" / "foo.pyi").exists()

    def test_project_directory_anchors_orphan_pruning_independent_of_cwd(
        self, *, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)
        out = Path("stubs")
        (tmp_path / out / "src" / "pkg").mkdir(parents=True)
        (tmp_path / out / "src" / "pkg" / "orphan.pyi").write_text(
            "# stale\n", encoding="utf-8"
        )

        changes = sync_stubs(
            python_files=[], output_dir=out, project_directory=tmp_path, check=False
        )

        assert changes == 1
        assert not (tmp_path / out / "src" / "pkg" / "orphan.pyi").exists()
        assert not (tmp_path / out / "src" / "pkg").exists()


class TestSyncStubsWithNoFiles:
    """sync_stubs with no files removes every stub, as when no root is left."""

    def _make_stubs(self, *, tmp_path, rel_pyis=("src/foo.pyi",)):
        """Create a stubs directory holding rel_pyis; return the directory."""
        stubs_dir = tmp_path / ".uncoded" / "stubs"
        for rel_pyi in rel_pyis:
            pyi = stubs_dir / rel_pyi
            pyi.parent.mkdir(parents=True, exist_ok=True)
            pyi.write_text("# stub\n", encoding="utf-8")
        return stubs_dir

    def _sync(self, *, tmp_path, check=False):
        return sync_stubs(
            python_files=[],
            output_dir=Path(".uncoded/stubs"),
            project_directory=tmp_path,
            check=check,
        )

    def test_changes_nothing_when_stubs_directory_absent(self, *, tmp_path):
        assert self._sync(tmp_path=tmp_path) == 0

    def test_removes_every_stub_and_directory(self, *, tmp_path):
        stubs_dir = self._make_stubs(
            tmp_path=tmp_path, rel_pyis=("src/a.pyi", "src/pkg/b.pyi")
        )
        assert self._sync(tmp_path=tmp_path) == 2
        assert not stubs_dir.exists()

    def test_check_mode_reports_without_removing(self, *, tmp_path):
        stubs_dir = self._make_stubs(tmp_path=tmp_path)
        assert self._sync(tmp_path=tmp_path, check=True) == 1
        assert (stubs_dir / "src" / "foo.pyi").exists()

    def test_stray_non_pyi_file_not_removed(self, *, tmp_path):
        stubs_dir = self._make_stubs(tmp_path=tmp_path)
        stray = stubs_dir / "src" / "stray.txt"
        stray.write_text("keep me\n", encoding="utf-8")
        assert self._sync(tmp_path=tmp_path) == 1
        assert not (stubs_dir / "src" / "foo.pyi").exists()
        assert stray.exists()
