import textwrap

import pytest

from uncoded.extract import (
    AssignmentSymbol,
    ClassSymbol,
    FunctionSymbol,
    Parameter,
    PropertySymbol,
    TypeAliasSymbol,
    _extract_python_file,
    read_python_files,
)
from uncoded.read_helpers import SkippedFile


def _names(*, symbols):
    return [symbol.name for symbol in symbols]


def _class(*, python_file, index=0):
    symbol = python_file.symbols[index]
    assert isinstance(symbol, ClassSymbol)
    return symbol


def _function(*, python_file, index=0):
    symbol = python_file.symbols[index]
    assert isinstance(symbol, FunctionSymbol)
    return symbol


class TestReadAndExtract:
    def test_keeps_each_python_file_that_has_symbols(self, *, tmp_path):
        # Simulate project structure: src/mypackage/...
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text(
            textwrap.dedent("""\
                class Engine:
                    def run(self):
                        pass

                def start():
                    pass
            """),
            encoding="utf-8",
        )
        (pkg / "_internal.py").write_text("def helper(): pass\n", encoding="utf-8")
        (pkg / "empty.py").write_text("# nothing here\n", encoding="utf-8")

        modules, _skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/core.py" in rel_paths
        assert "src/mypackage/_internal.py" in rel_paths
        assert any("__init__.py" in p for p in rel_paths) is False
        assert any("empty.py" in p for p in rel_paths) is False

    def test_nested_subpackage(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        sub = pkg / "utils"
        sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (sub / "__init__.py").write_text("", encoding="utf-8")
        (sub / "formatting.py").write_text(
            "def format_output(): pass\n", encoding="utf-8"
        )

        modules, _skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/utils/formatting.py" in rel_paths

    def test_includes_init_with_symbols(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("def create(): pass\n", encoding="utf-8")
        (pkg / "core.py").write_text("def run(): pass\n", encoding="utf-8")

        modules, _skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/__init__.py" in rel_paths
        assert "src/mypackage/core.py" in rel_paths

    def test_skips_empty_init(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text("def run(): pass\n", encoding="utf-8")

        modules, _skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        rel_paths = [m.rel_path for m in modules]
        assert not any("__init__.py" in p for p in rel_paths)

    def test_skips_syntax_errors(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "good.py").write_text("def works(): pass\n", encoding="utf-8")
        (pkg / "bad.py").write_text("def broken(:\n", encoding="utf-8")

        modules, skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/good.py" in rel_paths
        assert any("bad.py" in p for p in rel_paths) is False

        assert skipped == [
            SkippedFile(
                path="src/mypackage/bad.py",
                reason="SyntaxError at line 1: invalid syntax",
            )
        ]

    def test_skips_file_with_unknown_encoding(self, *, tmp_path):
        source_root = tmp_path / "src"
        bad_file = source_root / "bad's.py"
        bad_file.parent.mkdir()
        bad_file.write_text("# coding: unknown\n", encoding="utf-8")

        files, skipped = read_python_files(
            source_roots=[source_root], project_directory=tmp_path
        )

        assert files == []
        assert skipped == [
            SkippedFile(
                path="src/bad's.py",
                reason="SyntaxError: unknown encoding: unknown",
            )
        ]

    def test_skips_unreadable_file_with_reason(self, *, tmp_path):
        # A directory whose name ends in .py cannot be read as a file. The
        # reason leaves out the error's own copy of the path.
        (tmp_path / "src" / "pkg" / "notes.py").mkdir(parents=True)
        files, skipped = read_python_files(
            source_roots=[tmp_path / "src"], project_directory=tmp_path
        )
        assert files == []
        assert [s.path for s in skipped] == ["src/pkg/notes.py"]
        assert skipped[0].reason
        assert str(tmp_path) not in skipped[0].reason

    def test_skips_undecodable_file(self, *, tmp_path):
        # A file that cannot be decoded under its declared encoding (UTF-8
        # default) must be skipped; other files must still be read.
        src = tmp_path / "src"
        pkg = src / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "good.py").write_text("def works(): pass\n", encoding="utf-8")
        (pkg / "binary.py").write_bytes(b"\xff\xfe not utf-8")
        files, skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )
        assert [f.rel_path for f in files] == ["src/mypkg/good.py"]
        assert [s.path for s in skipped] == ["src/mypkg/binary.py"]

    def test_reads_latin1_declared_file(self, *, tmp_path):
        # A file that declares latin-1 encoding must be read and indexed,
        # not skipped; the declared encoding is honoured.
        src = tmp_path / "src"
        pkg = src / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "latin1.py").write_bytes(
            b"# -*- coding: latin-1 -*-\ndef caf\xe9(): pass\n"
        )
        files, skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )
        assert [f.rel_path for f in files] == ["src/mypkg/latin1.py"]
        assert skipped == []


class TestReadPythonFilesKeepsFilesWithSymbols:
    def test_keeps_a_file_with_only_assignments(self, *, tmp_path):
        pkg = tmp_path / "src" / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text('__version__ = "1.0"\n', encoding="utf-8")

        modules, _skipped = read_python_files(
            source_roots=[tmp_path / "src"], project_directory=tmp_path
        )

        assert [m.rel_path for m in modules] == ["src/mypackage/__init__.py"]

    def test_lists_files_in_path_order(self, *, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        for name in ("c", "a", "b"):
            (src / f"{name}.py").write_text(f"def {name}(): pass\n", encoding="utf-8")

        modules, _skipped = read_python_files(
            source_roots=[src], project_directory=tmp_path
        )

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py", "src/c.py"]
        assert _names(symbols=modules[0].symbols) == ["a"]


class TestExtractPythonFile:
    def test_extracts_function_signature(self):
        source = textwrap.dedent("""\
            def greet(name: str) -> str:
                '''Say hello.'''
                return f"Hello, {name}"
        """)
        module = _extract_python_file(source=source, rel_path="pkg/greet.py")
        f = _function(python_file=module)
        assert f.name == "greet"
        assert f.params == [Parameter("name", "str")]
        assert f.return_annotation == "str"

    def test_leaves_missing_function_annotations_empty(self):
        source = textwrap.dedent("""\
            def run(x, y):
                pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/run.py")
        f = _function(python_file=module)
        assert f.params == [Parameter("x"), Parameter("y")]
        assert f.return_annotation is None

    def test_extracts_async_functions_and_methods(self):
        source = textwrap.dedent("""\
            async def fetch_data(url: str) -> bytes:
                pass

            class Client:
                async def connect(self):
                    pass

                def disconnect(self):
                    pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/net.py")
        assert module.symbols == [
            FunctionSymbol(
                name="fetch_data",
                params=[Parameter("url", "str")],
                return_annotation="bytes",
                is_async=True,
            ),
            ClassSymbol(
                name="Client",
                members=[
                    FunctionSymbol(
                        name="connect",
                        params=[Parameter("self")],
                        is_async=True,
                    ),
                    FunctionSymbol(name="disconnect", params=[Parameter("self")]),
                ],
            ),
        ]

    def test_extracts_top_level_and_class_symbols(self):
        source = textwrap.dedent("""\
            class MyClass:
                def public_method(self):
                    pass

                def _private_method(self):
                    pass

            class _PrivateClass:
                def method(self):
                    pass

            def public_function():
                pass

            def _private_function():
                pass
        """)
        module = _extract_python_file(source=source, rel_path="module.py")
        assert module.rel_path == "module.py"
        assert module.symbols == [
            ClassSymbol(
                name="MyClass",
                members=[
                    FunctionSymbol(name="public_method", params=[Parameter("self")]),
                    FunctionSymbol(name="_private_method", params=[Parameter("self")]),
                ],
            ),
            ClassSymbol(
                name="_PrivateClass",
                members=[FunctionSymbol(name="method", params=[Parameter("self")])],
            ),
            FunctionSymbol(name="public_function"),
            FunctionSymbol(name="_private_function"),
        ]

    def test_extracts_class_assignments_and_methods(self):
        source = textwrap.dedent("""\
            class Record:
                '''Stores a named value.'''
                name: str
                value: int
                _internal: float

                def save(self) -> None:
                    '''Persist the record.'''
                    pass

                def _validate(self) -> bool:
                    pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/models.py")
        assert module.symbols == [
            ClassSymbol(
                name="Record",
                members=[
                    AssignmentSymbol(name="name", annotation="str"),
                    AssignmentSymbol(name="value", annotation="int"),
                    AssignmentSymbol(name="_internal", annotation="float"),
                    FunctionSymbol(
                        name="save",
                        params=[Parameter("self")],
                        return_annotation="None",
                    ),
                    FunctionSymbol(
                        name="_validate",
                        params=[Parameter("self")],
                        return_annotation="bool",
                    ),
                ],
            )
        ]

    def test_extracts_class_bases(self):
        source = textwrap.dedent("""\
            class Dog(Animal, Domestic):
                pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/animals.py")
        assert _class(python_file=module).bases == ["Animal", "Domestic"]

    def test_leaves_bases_empty_when_a_class_has_none(self):
        source = textwrap.dedent("""\
            class Plain:
                pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/plain.py")
        assert _class(python_file=module).bases == []

    def test_leaves_empty_module_without_symbols(self):
        module = _extract_python_file(source="", rel_path="empty.py")

        assert module.symbols == []

    def test_extracts_module_assignments(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
            MAX_RETRIES: int = 3
            __version__ = "1.0.0"
            _INTERNAL = 42
        """)
        module = _extract_python_file(source=source, rel_path="const.py")

        assert module.symbols == [
            AssignmentSymbol(name="TIMEOUT", value="30"),
            AssignmentSymbol(name="MAX_RETRIES", annotation="int", value="3"),
            AssignmentSymbol(name="__version__", value="'1.0.0'"),
            AssignmentSymbol(name="_INTERNAL", value="42"),
        ]

    def test_skips_chained_assignment(self):
        module = _extract_python_file(source="x = y = 1\n", rel_path="chain.py")

        assert module.symbols == []

    def test_extracts_non_property_decorated_method(self):
        source = textwrap.dedent("""\
            class Util:
                @staticmethod
                def helper():
                    pass
        """)
        module = _extract_python_file(source=source, rel_path="util.py")

        assert module.symbols == [
            ClassSymbol(name="Util", members=[FunctionSymbol(name="helper")])
        ]

    def test_preserves_module_and_class_member_order(self):
        source = textwrap.dedent("""\
            def zebra():
                pass

            class Alpha:
                def omega(self):
                    pass

                beta = 1

                def alpha(self):
                    pass

            ZETA = 1

            def apple():
                pass
        """)
        module = _extract_python_file(source=source, rel_path="ordering.py")

        assert module.symbols == [
            FunctionSymbol(name="zebra"),
            ClassSymbol(
                name="Alpha",
                members=[
                    FunctionSymbol(name="omega", params=[Parameter("self")]),
                    AssignmentSymbol(name="beta", value="1"),
                    FunctionSymbol(name="alpha", params=[Parameter("self")]),
                ],
            ),
            AssignmentSymbol(name="ZETA", value="1"),
            FunctionSymbol(name="apple"),
        ]

    def test_skips_non_symbol_statements(self):
        source = textwrap.dedent("""\
            import os
            from pathlib import Path

            class Registry:
                def __init__(self):
                    self.items = []

                class Entry:
                    pass

            def run():
                local = 1

            if os.name == "nt":
                SEPARATOR = ";"

            try:
                import tomllib
            except ImportError:
                FALLBACK = True
        """)
        module = _extract_python_file(source=source, rel_path="names.py")

        assert module.symbols == [
            ClassSymbol(
                name="Registry",
                members=[FunctionSymbol(name="__init__", params=[Parameter("self")])],
            ),
            FunctionSymbol(name="run"),
        ]

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param(
                "def f(x): pass\n",
                [Parameter("x")],
                id="regular_positional_bare",
            ),
            pytest.param(
                "def f(x: str): pass\n",
                [Parameter("x", "str")],
                id="regular_positional_annotated",
            ),
            pytest.param(
                "def f(x: int = 0): pass\n",
                [Parameter("x", "int")],
                id="defaults_dropped_positional",
            ),
            pytest.param(
                "def f(*args): pass\n",
                [Parameter("*args")],
                id="varargs_bare",
            ),
            pytest.param(
                "def f(*args: str): pass\n",
                [Parameter("*args", "str")],
                id="varargs_annotated",
            ),
            pytest.param(
                "def f(**kwargs): pass\n",
                [Parameter("**kwargs")],
                id="kwargs_bare",
            ),
            pytest.param(
                "def f(**kwargs: int): pass\n",
                [Parameter("**kwargs", "int")],
                id="kwargs_annotated",
            ),
            pytest.param(
                "def f(x, /): pass\n",
                [Parameter("x"), Parameter("/")],
                id="posonly_bare",
            ),
            pytest.param(
                "def f(x: str, /): pass\n",
                [Parameter("x", "str"), Parameter("/")],
                id="posonly_annotated",
            ),
            pytest.param(
                "def f(*, x): pass\n",
                [Parameter("*"), Parameter("x")],
                id="kwonly_bare",
            ),
            pytest.param(
                "def f(*, x: str): pass\n",
                [Parameter("*"), Parameter("x", "str")],
                id="kwonly_annotated",
            ),
            pytest.param(
                "def f(*, x: int = 0): pass\n",
                [Parameter("*"), Parameter("x", "int")],
                id="defaults_dropped_kwonly",
            ),
            pytest.param(
                "def f(*args, x): pass\n",
                [Parameter("*args"), Parameter("x")],
                id="vararg_with_kwonly",
            ),
            pytest.param(
                "def f(*args, **kwargs): pass\n",
                [Parameter("*args"), Parameter("**kwargs")],
                id="vararg_with_kwarg",
            ),
        ],
    )
    def test_extracts_each_kind_of_parameter(self, *, source, expected):
        module = _extract_python_file(source=source, rel_path="pkg/f.py")
        f = _function(python_file=module)
        assert f.params == expected

    def test_imports_collected(self):
        source = textwrap.dedent("""\
            import os
            from pathlib import Path
            from typing import Optional

            def run(p: Path) -> Optional[str]:
                pass
        """)
        module = _extract_python_file(source=source, rel_path="pkg/run.py")
        assert module.imports == [
            "import os",
            "from pathlib import Path",
            "from typing import Optional",
        ]

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            _extract_python_file(source="def broken(:\n", rel_path="pkg/bad.py")

    def test_assignment_bare_annotation(self):
        source = textwrap.dedent("""\
            FOO: int
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.symbols == [AssignmentSymbol(name="FOO", annotation="int")]

    def test_type_alias_classic(self):
        source = textwrap.dedent("""\
            from typing import TypeAlias
            UserId: TypeAlias = int
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.symbols == [
            AssignmentSymbol(name="UserId", annotation="TypeAlias", value="int")
        ]

    def test_type_alias_pep695(self):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.symbols == [TypeAliasSymbol(name="UserId", value="int")]

    def test_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            X, Y = 1, 2
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.symbols == []

    def test_annotation_whose_target_is_not_a_bare_name_skipped(self):
        source = "obj.x: int = 1\n"
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.symbols == []

    def test_class_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            class C:
                a, b = 1, 2
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        assert _class(python_file=module).members == []

    def test_class_with_unannotated_assignment(self):
        source = textwrap.dedent("""\
            class Registry:
                items = []
                count: int = 0
        """)
        module = _extract_python_file(source=source, rel_path="pkg/mod.py")
        cls = _class(python_file=module)
        names = [(a.name, a.annotation, a.value) for a in cls.members]
        assert names == [
            ("items", None, "[]"),
            ("count", "int", "0"),
        ]

    def test_property_is_indexed(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self) -> Path:
                    '''Return the configuration file path.'''
                    return self._path
        """)
        module = _extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = _class(python_file=module)
        assert cls.members == [PropertySymbol(name="path", annotation="Path")]

    def test_property_without_return_annotation(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path
        """)
        module = _extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = _class(python_file=module)
        assert cls.members == [PropertySymbol(name="path")]

    def test_property_setter_and_deleter_suppressed(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self) -> Path:
                    return self._path

                @path.setter
                def path(self, value: Path) -> None:
                    self._path = value

                @path.deleter
                def path(self) -> None:
                    del self._path
        """)
        module = _extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = _class(python_file=module)
        assert cls.members == [PropertySymbol(name="path", annotation="Path")]
