import ast
import textwrap
from unittest import mock

import pytest

from uncoded.body import (
    BodyNotFound,
    UnsupportedNamePath,
    resolve_ast_node,
    resolve_body,
    resolve_name_position,
)


class TestResolveBodyTopLevel:
    def test_function_without_decorators(self, tmp_path):
        source = textwrap.dedent("""\
            def foo():
                return 42
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("foo", path)

        assert result == "def foo():\n    return 42\n"

    def test_function_with_decorators(self, tmp_path):
        source = textwrap.dedent("""\
            import functools

            @functools.cache
            def compute():
                return 1
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("compute", path)

        assert result == "@functools.cache\ndef compute():\n    return 1\n"

    def test_async_function(self, tmp_path):
        source = textwrap.dedent("""\
            async def fetch():
                return 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("fetch", path)

        assert result == "async def fetch():\n    return 0\n"

    def test_class_whole_body(self, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                speed: int = 0

                def run(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Engine", path)

        assert result == source

    def test_module_constant_annotated(self, tmp_path):
        source = textwrap.dedent("""\
            MAX: int = 100
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("MAX", path)

        assert result == "MAX: int = 100\n"

    def test_module_constant_unannotated(self, tmp_path):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("TIMEOUT", path)

        assert result == "TIMEOUT = 30\n"

    def test_pep695_type_alias(self, tmp_path):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("UserId", path)

        assert result == "type UserId = int\n"

    def test_overload_returns_last_definition(self, tmp_path):
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
        path.write_text(source)

        result = resolve_body("process", path)

        assert result == "def process(x):\n    return x\n"

    def test_scans_past_non_matching_constant(self, tmp_path):
        source = textwrap.dedent("""\
            OTHER = 1

            def foo():
                return 42
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("foo", path)

        assert result == "def foo():\n    return 42\n"

    def test_not_found_raises_body_not_found(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def other(): pass\n")

        with pytest.raises(BodyNotFound, match="missing"):
            resolve_body("missing", path)

    def test_file_not_found_propagates(self, tmp_path):
        path = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            resolve_body("foo", path)

    def test_syntax_error_propagates(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def broken(:\n")

        with pytest.raises(SyntaxError):
            resolve_body("broken", path)


class TestResolveBodyClassMember:
    def test_method(self, tmp_path):
        source = textwrap.dedent("""\
            class Dog:
                def bark(self):
                    print("woof")
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Dog/bark", path)

        assert result == '    def bark(self):\n        print("woof")\n'

    def test_property_returns_getter_body(self, tmp_path):
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
        path.write_text(source)

        result = resolve_body("Config/path", path)

        expected = "    @property\n    def path(self):\n        return self._path\n"
        assert result == expected

    def test_class_attribute_annotated(self, tmp_path):
        source = textwrap.dedent("""\
            class Counter:
                count: int = 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Counter/count", path)

        assert result == "    count: int = 0\n"

    def test_class_attribute_unannotated(self, tmp_path):
        source = textwrap.dedent("""\
            class Config:
                debug = False
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Config/debug", path)

        assert result == "    debug = False\n"

    def test_scans_past_non_matching_attribute(self, tmp_path):
        source = textwrap.dedent("""\
            class Config:
                debug = False
                timeout = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Config/timeout", path)

        assert result == "    timeout = 30\n"

    def test_skips_non_function_nodes_in_class(self, tmp_path):
        source = textwrap.dedent("""\
            class Documented:
                \"\"\"A docstring.\"\"\"

                def method(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Documented/method", path)

        assert result == "    def method(self):\n        pass\n"

    def test_shadowed_class_member_found_in_last_definition(self, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def first_only(self):
                    pass

            class Foo:
                def second_only(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("Foo/second_only", path)

        assert result == "    def second_only(self):\n        pass\n"

    def test_shadowed_class_member_not_found_in_last_definition(self, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def first_only(self):
                    pass

            class Foo:
                def second_only(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        with pytest.raises(BodyNotFound, match="first_only"):
            resolve_body("Foo/first_only", path)

    def test_not_found_in_class(self, tmp_path):
        source = textwrap.dedent("""\
            class Foo:
                def bar(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        with pytest.raises(BodyNotFound, match="missing"):
            resolve_body("Foo/missing", path)


class TestUnsupportedNamePath:
    SUPPORTED_SHAPES = ("'name'", "'Class/member'")

    def _assert_raises(self, name_path, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def foo(): pass\n")
        with pytest.raises(UnsupportedNamePath) as exc_info:
            resolve_body(name_path, path)
        msg = str(exc_info.value)
        for shape in self.SUPPORTED_SHAPES:
            assert shape in msg

    def test_three_segment_path(self, tmp_path):
        self._assert_raises("A/B/C", tmp_path)

    def test_nested_class_shape(self, tmp_path):
        self._assert_raises("Outer/Inner/method", tmp_path)

    def test_empty_leading_segment(self, tmp_path):
        self._assert_raises("/foo", tmp_path)

    def test_empty_trailing_segment(self, tmp_path):
        self._assert_raises("foo/", tmp_path)

    def test_empty_middle_segment(self, tmp_path):
        self._assert_raises("foo//bar", tmp_path)


class TestResolveAstNode:
    def test_returns_function_def_for_top_level_function(self, tmp_path):
        source = textwrap.dedent("""\
            def compute(x: int) -> int:
                return x * 2
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        node = resolve_ast_node("compute", path)

        assert isinstance(node, ast.FunctionDef)
        assert node.name == "compute"

    def test_returns_method_node_for_class_member(self, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                def start(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        node = resolve_ast_node("Engine/start", path)

        assert isinstance(node, ast.FunctionDef)
        assert node.name == "start"

    def test_raises_body_not_found(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def other(): pass\n")

        with pytest.raises(BodyNotFound, match="missing"):
            resolve_ast_node("missing", path)

    def test_raises_unsupported_name_path(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def foo(): pass\n")

        with pytest.raises(UnsupportedNamePath):
            resolve_ast_node("A/B/C", path)

    def test_file_not_found_propagates(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            resolve_ast_node("foo", tmp_path / "nonexistent.py")

    def test_syntax_error_propagates(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("def broken(:\n")

        with pytest.raises(SyntaxError):
            resolve_ast_node("broken", path)


class TestResolveNamePosition:
    def test_function(self, tmp_path):
        source = textwrap.dedent("""\
            def compute(x: int) -> int:
                return x * 2
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("compute", path) == (0, 4)

    def test_function_decorator_does_not_shift_line(self, tmp_path):
        source = textwrap.dedent("""\
            import functools

            @functools.cache
            def compute():
                return 1
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("compute", path) == (3, 4)

    def test_async_function(self, tmp_path):
        source = textwrap.dedent("""\
            async def fetch():
                return 0
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("fetch", path) == (0, 10)

    def test_class(self, tmp_path):
        source = textwrap.dedent("""\
            class Engine:
                pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("Engine", path) == (0, 6)

    def test_annotated_assignment(self, tmp_path):
        source = textwrap.dedent("""\
            MAX: int = 100
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("MAX", path) == (0, 0)

    def test_unannotated_assignment(self, tmp_path):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("TIMEOUT", path) == (0, 0)

    def test_type_alias(self, tmp_path):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("UserId", path) == (0, 5)

    def test_class_method(self, tmp_path):
        source = textwrap.dedent("""\
            class Dog:
                def bark(self):
                    pass
        """)
        path = tmp_path / "m.py"
        path.write_text(source)

        assert resolve_name_position("Dog/bark", path) == (1, 8)

    def test_unexpected_node_type_raises_unsupported_name_path(self, tmp_path):
        path = tmp_path / "m.py"
        path.write_text("pass\n")

        with (
            mock.patch("uncoded.body.resolve_ast_node", return_value=ast.Pass()),
            pytest.raises(UnsupportedNamePath),
        ):
            resolve_name_position("anything", path)


class TestResolveBodyByteIdentical:
    def test_exact_source_returned(self, tmp_path):
        body = "def compute(x: int) -> int:\n    result = x * 2\n    return result\n"
        source = f"# header\n\n{body}\n# footer\n"
        path = tmp_path / "m.py"
        path.write_text(source)

        result = resolve_body("compute", path)

        assert result == body
