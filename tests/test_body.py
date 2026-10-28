import ast
import textwrap

import pytest

from uncoded.body import resolve_definition
from uncoded.resolver import (
    NamePath,
    SymbolNotFoundError,
    UnsupportedNamePathError,
    _resolve_ast_node,
    resolve_name_position,
)


class TestResolveDefinitionTopLevel:
    def test_function_without_decorators(self, *, tmp_path):
        source = textwrap.dedent("""\
            def foo():
                return 42
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("foo"), in_path=path)

        assert result == "def foo():\n    return 42\n"

    def test_function_with_decorators(self, *, tmp_path):
        source = textwrap.dedent("""\
            import functools

            @functools.cache
            def compute():
                return 1
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("compute"), in_path=path)

        assert result == "@functools.cache\ndef compute():\n    return 1\n"

    def test_async_function(self, *, tmp_path):
        source = textwrap.dedent("""\
            async def fetch():
                return 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("fetch"), in_path=path)

        assert result == "async def fetch():\n    return 0\n"

    def test_class_whole_definition(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                speed: int = 0

                def run(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("Engine"), in_path=path)

        assert result == source

    def test_module_level_assignment_annotated(self, *, tmp_path):
        source = textwrap.dedent("""\
            MAX: int = 100
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("MAX"), in_path=path)

        assert result == "MAX: int = 100\n"

    def test_module_level_assignment_unannotated(self, *, tmp_path):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("TIMEOUT"), in_path=path)

        assert result == "TIMEOUT = 30\n"

    def test_pep695_type_alias(self, *, tmp_path):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("UserId"), in_path=path)

        assert result == "type UserId = int\n"

    def test_overload_returns_last_definition(self, *, tmp_path):
        source = textwrap.dedent("""\
            from typing import overload

            @overload
            def process(x: int) -> int: ...

            @overload
            def process(x: str) -> str: ...

            def process(x):
                return x
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("process"), in_path=path)

        assert result == "def process(x):\n    return x\n"

    def test_scans_past_non_matching_assignment(self, *, tmp_path):
        source = textwrap.dedent("""\
            OTHER = 1

            def foo():
                return 42
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("foo"), in_path=path)

        assert result == "def foo():\n    return 42\n"

    def test_not_found_raises_symbol_not_found(self, *, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def other(): pass\n", encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError, match="missing"):
            resolve_definition(name_path=NamePath("missing"), in_path=path)

    @pytest.mark.parametrize("source", ["x, y = 1, 2\n", "x = y = 1\n"])
    def test_name_bound_with_others_is_not_found(self, *, tmp_path, source):
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError):
            resolve_definition(name_path=NamePath("x"), in_path=path)

    def test_raises_when_the_file_is_missing(self, *, tmp_path):
        path = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            resolve_definition(name_path=NamePath("foo"), in_path=path)

    def test_raises_when_the_file_cannot_be_parsed(self, *, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def broken(:\n", encoding="utf-8", newline="")

        with pytest.raises(SyntaxError):
            resolve_definition(name_path=NamePath("broken"), in_path=path)

    def test_reads_latin1_declared_file(self, *, tmp_path):
        # A file that declares latin-1 encoding must be read under that
        # encoding and return correctly decoded source.
        path = tmp_path / "m.py"
        path.write_bytes(b"# -*- coding: latin-1 -*-\ndef caf\xe9(): pass\n")

        result = resolve_definition(name_path=NamePath("café"), in_path=path)

        assert result == "def café(): pass\n"

    def test_prints_whole_lines(self, *, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("x = 1; y = 2\n", encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("x"), in_path=path)

        assert result == "x = 1; y = 2\n"


class TestResolveDefinitionClassMember:
    def test_method(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Dog:
                def bark(self):
                    print("woof")
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("Dog", "bark"), in_path=path)

        assert result == '    def bark(self):\n        print("woof")\n'

    def test_property_returns_getter_definition(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path

                @path.setter
                def path(self, value):
                    self._path = value
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("Config", "path"), in_path=path)

        expected = "    @property\n    def path(self):\n        return self._path\n"
        assert result == expected

    def test_class_assignment_annotated(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Counter:
                count: int = 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(
            name_path=NamePath("Counter", "count"), in_path=path
        )

        assert result == "    count: int = 0\n"

    def test_class_assignment_unannotated(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Config:
                debug = False
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("Config", "debug"), in_path=path)

        assert result == "    debug = False\n"

    def test_scans_past_non_matching_assignment(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Config:
                debug = False
                timeout = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(
            name_path=NamePath("Config", "timeout"), in_path=path
        )

        assert result == "    timeout = 30\n"

    def test_skips_non_function_nodes_in_class(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Documented:
                \"\"\"A docstring.\"\"\"

                def method(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(
            name_path=NamePath("Documented", "method"), in_path=path
        )

        assert result == "    def method(self):\n        pass\n"

    def test_redefined_class_member_found_in_last_definition(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def first_only(self):
                    pass

            class Foo:
                def second_only(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(
            name_path=NamePath("Foo", "second_only"), in_path=path
        )

        assert result == "    def second_only(self):\n        pass\n"

    def test_redefined_class_member_not_found_in_last_definition(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def first_only(self):
                    pass

            class Foo:
                def second_only(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError, match="first_only"):
            resolve_definition(name_path=NamePath("Foo", "first_only"), in_path=path)

    def test_not_found_in_class(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def bar(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError, match="missing"):
            resolve_definition(name_path=NamePath("Foo", "missing"), in_path=path)

    @pytest.mark.parametrize(
        "redefinition",
        ["def Foo(): pass\n", "Foo = 1\n", "Foo: int\n", "type Foo = int\n"],
    )
    def test_member_of_class_that_a_later_definition_redefines_is_not_found(
        self, *, tmp_path, redefinition
    ):
        source = "class Foo:\n    member = 1\n\n" + redefinition
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError, match="Foo/member"):
            resolve_definition(name_path=NamePath("Foo", "member"), in_path=path)

    def test_member_found_when_class_redefines_a_function(self, *, tmp_path):
        source = textwrap.dedent("""\
            def Foo(): pass

            class Foo:
                def member(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("Foo", "member"), in_path=path)

        assert result == "    def member(self):\n        pass\n"


class TestUnsupportedNamePathError:
    SUPPORTED_SHAPES = ("'name'", "'Class/member'")

    def _assert_raises(self, *, name_path):
        with pytest.raises(UnsupportedNamePathError) as exc_info:
            NamePath.parse(raw=name_path)
        msg = str(exc_info.value)
        for shape in self.SUPPORTED_SHAPES:
            assert shape in msg

    def test_three_segment_path(self):
        self._assert_raises(name_path="A/B/C")

    def test_nested_class_shape(self):
        self._assert_raises(name_path="Outer/Inner/method")

    def test_empty_leading_segment(self):
        self._assert_raises(name_path="/foo")

    def test_empty_trailing_segment(self):
        self._assert_raises(name_path="foo/")

    def test_empty_middle_segment(self):
        self._assert_raises(name_path="foo//bar")


class TestResolveAstNode:
    def test_returns_function_def_for_top_level_function(self, *, tmp_path):
        source = textwrap.dedent("""\
            def compute(x: int) -> int:
                return x * 2
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        node = _resolve_ast_node(name_path=NamePath("compute"), in_path=path)

        assert isinstance(node, ast.FunctionDef)
        assert node.name == "compute"

    def test_returns_method_node_for_class_member(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                def start(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        node = _resolve_ast_node(name_path=NamePath("Engine", "start"), in_path=path)

        assert isinstance(node, ast.FunctionDef)
        assert node.name == "start"

    def test_raises_symbol_not_found(self, *, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def other(): pass\n", encoding="utf-8", newline="")

        with pytest.raises(SymbolNotFoundError, match="missing"):
            _resolve_ast_node(name_path=NamePath("missing"), in_path=path)

    def test_raises_unsupported_name_path(self):
        with pytest.raises(UnsupportedNamePathError):
            NamePath.parse(raw="A/B/C")

    def test_raises_when_the_file_is_missing(self, *, tmp_path):
        with pytest.raises(FileNotFoundError):
            _resolve_ast_node(
                name_path=NamePath("foo"), in_path=tmp_path / "nonexistent.py"
            )

    def test_raises_when_the_file_cannot_be_parsed(self, *, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def broken(:\n", encoding="utf-8", newline="")

        with pytest.raises(SyntaxError):
            _resolve_ast_node(name_path=NamePath("broken"), in_path=path)


class TestResolveNamePosition:
    def test_function(self, *, tmp_path):
        source = textwrap.dedent("""\
            def compute(x: int) -> int:
                return x * 2
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("compute"), in_path=path) == (
            0,
            4,
        )

    def test_function_decorator_does_not_shift_line(self, *, tmp_path):
        source = textwrap.dedent("""\
            import functools

            @functools.cache
            def compute():
                return 1
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("compute"), in_path=path) == (
            3,
            4,
        )

    def test_async_function(self, *, tmp_path):
        source = textwrap.dedent("""\
            async def fetch():
                return 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("fetch"), in_path=path) == (
            0,
            10,
        )

    def test_class(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("Engine"), in_path=path) == (
            0,
            6,
        )

    def test_annotated_assignment(self, *, tmp_path):
        source = textwrap.dedent("""\
            MAX: int = 100
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("MAX"), in_path=path) == (0, 0)

    def test_unannotated_assignment(self, *, tmp_path):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("TIMEOUT"), in_path=path) == (
            0,
            0,
        )

    def test_type_alias(self, *, tmp_path):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(name_path=NamePath("UserId"), in_path=path) == (
            0,
            5,
        )

    def test_method(self, *, tmp_path):
        source = textwrap.dedent("""\
            class Dog:
                def bark(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        assert resolve_name_position(
            name_path=NamePath("Dog", "bark"), in_path=path
        ) == (1, 8)


class TestResolveDefinitionExactlyAsInTheFile:
    def test_exact_source_returned(self, *, tmp_path):
        definition = (
            "def compute(x: int) -> int:\n    result = x * 2\n    return result\n"
        )
        source = f"# header\n\n{definition}\n# footer\n"
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("compute"), in_path=path)

        assert result == definition

    @pytest.mark.parametrize("line_ending", ["\r\n", "\r"])
    def test_keeps_line_endings(self, *, tmp_path, line_ending):
        definition = f"def compute():{line_ending}    return 1{line_ending}"
        source = f"# header{line_ending}{definition}# footer{line_ending}"
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("compute"), in_path=path)

        assert result == definition

    def test_leaves_out_byte_order_mark(self, *, tmp_path):
        definition = "def compute():\n    return 1\n"
        path = tmp_path / "m.py"
        path.write_bytes(b"\xef\xbb\xbf" + definition.encode("utf-8"))

        result = resolve_definition(name_path=NamePath("compute"), in_path=path)

        assert result == definition

    def test_lines_are_counted_as_python_counts_them(self, *, tmp_path):
        # A form feed and a line separator do not end a line in Python.
        definition = "def compute():\x0c\n    return 1\n"
        source = f'x = "a\u2028b"\n{definition}'
        path = tmp_path / "m.py"
        path.write_text(source, encoding="utf-8", newline="")

        result = resolve_definition(name_path=NamePath("compute"), in_path=path)

        assert result == definition
