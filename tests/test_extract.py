import textwrap

import pytest

from uncoded.extract import (
    AssignmentSymbol,
    Parameter,
    TypeAliasSymbol,
    extract_python_file,
    extract_python_files,
    read_source_files,
)
from uncoded.read_helpers import SkippedFile


def _names(*, symbols):
    return [symbol.name for symbol in symbols]


class TestWhichStatementsAreSymbols:
    def test_classes_and_functions(self):
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

        result = extract_python_file(source=source, rel_path="module.py")

        assert result.rel_path == "module.py"
        assert len(result.classes) == 2
        assert result.classes[0].name == "MyClass"
        assert _names(symbols=result.classes[0].methods) == [
            "public_method",
            "_private_method",
        ]
        assert result.classes[1].name == "_PrivateClass"
        assert _names(symbols=result.classes[1].methods) == ["method"]
        assert _names(symbols=result.functions) == [
            "public_function",
            "_private_function",
        ]

    def test_async_functions_and_methods(self):
        source = textwrap.dedent("""\
            async def fetch_data():
                pass

            class Client:
                async def connect(self):
                    pass

                def disconnect(self):
                    pass
        """)

        result = extract_python_file(source=source, rel_path="async_module.py")

        assert _names(symbols=result.functions) == ["fetch_data"]
        assert result.classes[0].name == "Client"
        assert _names(symbols=result.classes[0].methods) == ["connect", "disconnect"]

    def test_empty_module(self):
        result = extract_python_file(source="", rel_path="empty.py")

        assert result.classes == []
        assert _names(symbols=result.functions) == []

    def test_module_level_assignments(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
            MAX_RETRIES: int = 3
            __version__ = "1.0.0"
        """)

        result = extract_python_file(source=source, rel_path="const.py")

        assert _names(symbols=result.assignments) == [
            "TIMEOUT",
            "MAX_RETRIES",
            "__version__",
        ]

    def test_chained_assignment_skipped(self):
        source = "x = y = 1\n"

        result = extract_python_file(source=source, rel_path="chain.py")

        assert _names(symbols=result.assignments) == []

    def test_non_property_decorator_classified_as_method(self):
        source = textwrap.dedent("""\
            class Util:
                @staticmethod
                def helper():
                    pass
        """)

        result = extract_python_file(source=source, rel_path="util.py")

        cls = result.classes[0]
        assert _names(symbols=cls.methods) == ["helper"]
        assert _names(symbols=cls.attributes) == []

    def test_preserves_source_order(self):
        source = textwrap.dedent("""\
            def zebra():
                pass

            class Alpha:
                def omega(self):
                    pass

                def alpha(self):
                    pass

            def apple():
                pass
        """)

        result = extract_python_file(source=source, rel_path="ordering.py")

        assert _names(symbols=result.functions) == ["zebra", "apple"]
        assert _names(symbols=result.classes[0].methods) == ["omega", "alpha"]

    def test_leaves_out_names_that_are_not_symbols(self):
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

        result = extract_python_file(source=source, rel_path="names.py")

        assert _names(symbols=result.assignments) == []
        assert _names(symbols=result.classes) == ["Registry"]
        assert _names(symbols=result.classes[0].attributes) == []
        assert _names(symbols=result.classes[0].methods) == ["__init__"]
        assert _names(symbols=result.functions) == ["run"]


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

        files, _skipped = read_source_files(source_root=src, project_directory=tmp_path)
        modules = extract_python_files(files=files)

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

        files, _skipped = read_source_files(source_root=src, project_directory=tmp_path)
        modules = extract_python_files(files=files)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/utils/formatting.py" in rel_paths

    def test_includes_init_with_symbols(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("def create(): pass\n", encoding="utf-8")
        (pkg / "core.py").write_text("def run(): pass\n", encoding="utf-8")

        files, _skipped = read_source_files(source_root=src, project_directory=tmp_path)
        modules = extract_python_files(files=files)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/__init__.py" in rel_paths
        assert "src/mypackage/core.py" in rel_paths

    def test_skips_empty_init(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "core.py").write_text("def run(): pass\n", encoding="utf-8")

        files, _skipped = read_source_files(source_root=src, project_directory=tmp_path)
        modules = extract_python_files(files=files)

        rel_paths = [m.rel_path for m in modules]
        assert not any("__init__.py" in p for p in rel_paths)

    def test_skips_syntax_errors(self, *, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "good.py").write_text("def works(): pass\n", encoding="utf-8")
        (pkg / "bad.py").write_text("def broken(:\n", encoding="utf-8")

        files, skipped = read_source_files(source_root=src, project_directory=tmp_path)
        modules = extract_python_files(files=files)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/good.py" in rel_paths
        assert any("bad.py" in p for p in rel_paths) is False

        assert skipped == [
            SkippedFile(
                path="src/mypackage/bad.py",
                reason="SyntaxError at line 1: invalid syntax",
            )
        ]

    def test_skips_unreadable_file_with_reason(self, *, tmp_path):
        # A directory whose name ends in .py cannot be read as a file. The
        # reason leaves out the error's own copy of the path.
        (tmp_path / "src" / "pkg" / "notes.py").mkdir(parents=True)
        files, skipped = read_source_files(
            source_root=tmp_path / "src", project_directory=tmp_path
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
        files, skipped = read_source_files(source_root=src, project_directory=tmp_path)
        assert [rel for _, rel in files] == ["src/mypkg/good.py"]
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
        files, skipped = read_source_files(source_root=src, project_directory=tmp_path)
        assert [rel for _, rel in files] == ["src/mypkg/latin1.py"]
        assert skipped == []


class TestExtractPythonFiles:
    def test_extracts_the_symbols_of_each_file(self):
        files = [
            ("def foo(): pass\n", "src/a.py"),
            ("class Bar: pass\n", "src/b.py"),
        ]

        modules = extract_python_files(files=files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py"]
        assert _names(symbols=modules[0].functions) == ["foo"]
        assert modules[1].classes[0].name == "Bar"

    def test_preserves_source_order(self):
        files = [
            ("def a(): pass\n", "src/a.py"),
            ("def b(): pass\n", "src/b.py"),
            ("def c(): pass\n", "src/c.py"),
        ]

        modules = extract_python_files(files=files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py", "src/c.py"]

    def test_module_with_only_assignments_is_kept(self):
        files = [('__version__ = "1.0"\n', "src/mypackage/__init__.py")]

        modules = extract_python_files(files=files)

        assert [m.rel_path for m in modules] == ["src/mypackage/__init__.py"]

    def test_skips_files_with_no_symbols(self):
        files = [
            ("def foo(): pass\n", "src/a.py"),
            ("# nothing here\n", "src/empty.py"),
            ("class Bar: pass\n", "src/b.py"),
        ]

        modules = extract_python_files(files=files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py"]


class TestExtractPythonFile:
    def test_simple_function(self):
        source = textwrap.dedent("""\
            def greet(name: str) -> str:
                '''Say hello.'''
                return f"Hello, {name}"
        """)
        module = extract_python_file(source=source, rel_path="pkg/greet.py")
        assert len(module.functions) == 1
        f = module.functions[0]
        assert f.name == "greet"
        assert f.params == [Parameter("name", "str")]
        assert f.return_annotation == "str"

    def test_function_no_annotations(self):
        source = textwrap.dedent("""\
            def run(x, y):
                pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/run.py")
        f = module.functions[0]
        assert f.params == [Parameter("x"), Parameter("y")]
        assert f.return_annotation is None

    def test_async_function(self):
        source = textwrap.dedent("""\
            async def fetch(url: str) -> bytes:
                pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/net.py")
        f = module.functions[0]
        assert f.is_async is True
        assert f.name == "fetch"

    def test_private_function_included(self):
        source = textwrap.dedent("""\
            def public(): pass
            def _private(): pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert len(module.functions) == 2
        assert module.functions[0].name == "public"
        assert module.functions[1].name == "_private"

    def test_class_with_attributes_and_methods(self):
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
        module = extract_python_file(source=source, rel_path="pkg/models.py")
        assert len(module.classes) == 1
        cls = module.classes[0]
        assert cls.name == "Record"
        assert [(a.name, a.annotation) for a in cls.attributes] == [
            ("name", "str"),
            ("value", "int"),
            ("_internal", "float"),
        ]
        assert [m.name for m in cls.methods] == ["save", "_validate"]

    def test_class_with_bases(self):
        source = textwrap.dedent("""\
            class Dog(Animal, Domestic):
                pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/animals.py")
        assert module.classes[0].bases == ["Animal", "Domestic"]

    def test_class_no_bases(self):
        source = textwrap.dedent("""\
            class Plain:
                pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/plain.py")
        assert module.classes[0].bases == []

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
        module = extract_python_file(source=source, rel_path="pkg/f.py")
        f = module.functions[0]
        assert f.params == expected

    def test_imports_collected(self):
        source = textwrap.dedent("""\
            import os
            from pathlib import Path
            from typing import Optional

            def run(p: Path) -> Optional[str]:
                pass
        """)
        module = extract_python_file(source=source, rel_path="pkg/run.py")
        assert module.imports == [
            "import os",
            "from pathlib import Path",
            "from typing import Optional",
        ]

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            extract_python_file(source="def broken(:\n", rel_path="pkg/bad.py")

    def test_assignment_annotated_with_value(self):
        source = textwrap.dedent("""\
            MAX_RETRIES: int = 3
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == [
            AssignmentSymbol(name="MAX_RETRIES", annotation="int", value="3")
        ]

    def test_assignment_unannotated_with_value(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == [AssignmentSymbol(name="TIMEOUT", value="30")]

    def test_assignment_bare_annotation(self):
        source = textwrap.dedent("""\
            FOO: int
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == [AssignmentSymbol(name="FOO", annotation="int")]

    def test_assignment_private_included(self):
        source = textwrap.dedent("""\
            _INTERNAL = 42
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments[0].name == "_INTERNAL"

    def test_type_alias_classic(self):
        source = textwrap.dedent("""\
            from typing import TypeAlias
            UserId: TypeAlias = int
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == [
            AssignmentSymbol(name="UserId", annotation="TypeAlias", value="int")
        ]

    def test_type_alias_pep695(self):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == [TypeAliasSymbol(name="UserId", value="int")]

    def test_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            X, Y = 1, 2
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == []

    def test_annotation_whose_target_is_not_a_bare_name_skipped(self):
        source = "obj.x: int = 1\n"
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.assignments == []

    def test_class_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            class C:
                a, b = 1, 2
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        assert module.classes[0].attributes == []

    def test_class_with_unannotated_attribute(self):
        source = textwrap.dedent("""\
            class Registry:
                items = []
                count: int = 0
        """)
        module = extract_python_file(source=source, rel_path="pkg/mod.py")
        cls = module.classes[0]
        names = [(a.name, a.annotation, a.value) for a in cls.attributes]
        assert names == [
            ("items", None, "[]"),
            ("count", "int", "0"),
        ]

    def test_property_rendered_as_attribute(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self) -> Path:
                    '''Return the configuration file path.'''
                    return self._path
        """)
        module = extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = module.classes[0]
        assert cls.methods == []
        assert len(cls.attributes) == 1
        attr = cls.attributes[0]
        assert attr.name == "path"
        assert attr.annotation == "Path"
        assert attr.value is None

    def test_property_without_return_annotation(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path
        """)
        module = extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = module.classes[0]
        assert cls.attributes[0].name == "path"
        assert cls.attributes[0].annotation is None

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
        module = extract_python_file(source=source, rel_path="pkg/cfg.py")
        cls = module.classes[0]
        assert [a.name for a in cls.attributes] == ["path"]
        assert cls.methods == []
