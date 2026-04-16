import textwrap

import pytest

from uncoded.stubs import (
    StubAssignment,
    StubClass,
    StubFunction,
    StubModule,
    StubParam,
    extract_stub,
    render_stub,
)


class TestExtractStub:
    def test_simple_function(self):
        source = textwrap.dedent("""\
            def greet(name: str) -> str:
                '''Say hello.'''
                return f"Hello, {name}"
        """)
        module = extract_stub(source, "pkg/greet.py")
        assert len(module.functions) == 1
        f = module.functions[0]
        assert f.name == "greet"
        assert f.params == [StubParam("name", "str")]
        assert f.return_annotation == "str"
        assert f.docstring_excerpt == "Say hello."
        assert f.start_line == 1
        assert f.end_line == 3

    def test_function_no_annotations(self):
        source = textwrap.dedent("""\
            def run(x, y):
                pass
        """)
        module = extract_stub(source, "pkg/run.py")
        f = module.functions[0]
        assert f.params == [StubParam("x"), StubParam("y")]
        assert f.return_annotation is None

    def test_async_function(self):
        source = textwrap.dedent("""\
            async def fetch(url: str) -> bytes:
                pass
        """)
        module = extract_stub(source, "pkg/net.py")
        f = module.functions[0]
        assert f.is_async is True
        assert f.name == "fetch"

    def test_private_function_included(self):
        source = textwrap.dedent("""\
            def public(): pass
            def _private(): pass
        """)
        module = extract_stub(source, "pkg/mod.py")
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
        module = extract_stub(source, "pkg/models.py")
        assert len(module.classes) == 1
        cls = module.classes[0]
        assert cls.name == "Record"
        assert cls.docstring_excerpt == "Stores a named value."
        assert [(a.name, a.annotation) for a in cls.attributes] == [
            ("name", "str"),
            ("value", "int"),
            ("_internal", "float"),
        ]
        assert len(cls.methods) == 2
        assert cls.methods[0].name == "save"
        assert cls.methods[1].name == "_validate"

    def test_class_line_range(self):
        source = textwrap.dedent("""\
            class Foo:
                def bar(self):
                    pass

                def baz(self):
                    pass
        """)
        module = extract_stub(source, "pkg/foo.py")
        cls = module.classes[0]
        assert cls.start_line == 1
        assert cls.end_line == 6
        assert cls.methods[0].start_line == 2
        assert cls.methods[0].end_line == 3
        assert cls.methods[1].start_line == 5
        assert cls.methods[1].end_line == 6

    def test_class_with_bases(self):
        source = textwrap.dedent("""\
            class Dog(Animal, Domestic):
                pass
        """)
        module = extract_stub(source, "pkg/animals.py")
        assert module.classes[0].bases == ["Animal", "Domestic"]

    def test_class_no_bases(self):
        source = textwrap.dedent("""\
            class Plain:
                pass
        """)
        module = extract_stub(source, "pkg/plain.py")
        assert module.classes[0].bases == []

    def test_docstring_first_sentence_only(self):
        source = textwrap.dedent("""\
            def process():
                '''Parse the input. Then validate it. Then return.'''
                pass
        """)
        module = extract_stub(source, "pkg/proc.py")
        assert module.functions[0].docstring_excerpt == "Parse the input."

    def test_no_docstring(self):
        source = textwrap.dedent("""\
            def silent():
                pass
        """)
        module = extract_stub(source, "pkg/silent.py")
        assert module.functions[0].docstring_excerpt is None

    def test_kwargs_and_varargs(self):
        source = textwrap.dedent("""\
            def build(*args: str, **kwargs: int) -> None:
                pass
        """)
        module = extract_stub(source, "pkg/build.py")
        f = module.functions[0]
        assert StubParam("*args", "str") in f.params
        assert StubParam("**kwargs", "int") in f.params

    def test_imports_collected(self):
        source = textwrap.dedent("""\
            import os
            from pathlib import Path
            from typing import Optional

            def run(p: Path) -> Optional[str]:
                pass
        """)
        module = extract_stub(source, "pkg/run.py")
        assert module.imports == [
            "import os",
            "from pathlib import Path",
            "from typing import Optional",
        ]

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            extract_stub("def broken(:\n", "pkg/bad.py")

    def test_source_order_preserved(self):
        source = textwrap.dedent("""\
            def zebra(): pass
            class Alpha: pass
            def apple(): pass
        """)
        module = extract_stub(source, "pkg/mixed.py")
        assert module.functions[0].name == "zebra"
        assert module.functions[1].name == "apple"
        assert module.classes[0].name == "Alpha"

    def test_constant_annotated_with_value(self):
        source = textwrap.dedent("""\
            MAX_RETRIES: int = 3
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "MAX_RETRIES"
        assert c.annotation == "int"
        assert c.value_source == "3"
        assert c.is_type_alias is False
        assert c.start_line == 1

    def test_constant_unannotated_with_value(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "TIMEOUT"
        assert c.annotation is None
        assert c.value_source == "30"

    def test_constant_bare_annotation(self):
        source = textwrap.dedent("""\
            FOO: int
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.annotation == "int"
        assert c.value_source is None

    def test_constant_value_too_long_elided(self):
        long_list = "[" + ", ".join(f'"item{i}"' for i in range(50)) + "]"
        source = f"BIG = {long_list}\n"
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "BIG"
        assert c.value_source == "..."

    def test_constant_private_included(self):
        source = textwrap.dedent("""\
            _INTERNAL = 42
        """)
        module = extract_stub(source, "pkg/mod.py")
        assert module.constants[0].name == "_INTERNAL"

    def test_type_alias_classic(self):
        source = textwrap.dedent("""\
            from typing import TypeAlias
            UserId: TypeAlias = int
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "UserId"
        assert c.annotation == "TypeAlias"
        assert c.value_source == "int"
        assert c.is_type_alias is False

    def test_type_alias_pep695(self):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "UserId"
        assert c.is_type_alias is True
        assert c.value_source == "int"

    def test_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            X, Y = 1, 2
        """)
        module = extract_stub(source, "pkg/mod.py")
        assert module.constants == []

    def test_class_with_unannotated_attribute(self):
        source = textwrap.dedent("""\
            class Registry:
                items = []
                count: int = 0
        """)
        module = extract_stub(source, "pkg/mod.py")
        cls = module.classes[0]
        names = [(a.name, a.annotation, a.value_source) for a in cls.attributes]
        assert names == [
            ("items", None, "[]"),
            ("count", "int", "0"),
        ]

    def test_property_rendered_as_attribute(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self) -> Path:
                    '''Return the config file path.'''
                    return self._path
        """)
        module = extract_stub(source, "pkg/cfg.py")
        cls = module.classes[0]
        assert cls.methods == []
        assert len(cls.attributes) == 1
        attr = cls.attributes[0]
        assert attr.name == "path"
        assert attr.annotation == "Path"
        assert attr.value_source is None

    def test_property_without_return_annotation(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path
        """)
        module = extract_stub(source, "pkg/cfg.py")
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
        module = extract_stub(source, "pkg/cfg.py")
        cls = module.classes[0]
        assert [a.name for a in cls.attributes] == ["path"]
        assert cls.methods == []


class TestRenderStub:
    def test_header_contains_path(self):
        module = StubModule(rel_path="src/pkg/mod.py")
        assert render_stub(module).startswith("# src/pkg/mod.py")

    def test_imports_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            imports=["import os", "from pathlib import Path"],
        )
        output = render_stub(module)
        assert "import os\nfrom pathlib import Path" in output

    def test_function_line_range(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="run", start_line=10, end_line=20)],
        )
        output = render_stub(module)
        assert "def run():  # L10-20\n    ..." in output

    def test_async_function_prefix(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[
                StubFunction(name="fetch", is_async=True, start_line=1, end_line=3)
            ],
        )
        assert "async def fetch" in render_stub(module)

    def test_function_with_annotations(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[
                StubFunction(
                    name="greet",
                    params=[StubParam("name", "str")],
                    return_annotation="str",
                    start_line=1,
                    end_line=2,
                )
            ],
        )
        assert "def greet(name: str) -> str:" in render_stub(module)

    def test_docstring_excerpt_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[
                StubFunction(
                    name="go",
                    docstring_excerpt="Do the thing.",
                    start_line=1,
                    end_line=3,
                )
            ],
        )
        output = render_stub(module)
        assert '"""Do the thing."""' in output
        assert '"""Do the thing."""\n    ...' in output

    def test_class_with_bases(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Dog", bases=["Animal"], start_line=1, end_line=5)],
        )
        assert "class Dog(Animal):  # L1-5" in render_stub(module)

    def test_class_single_line_range(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Marker", start_line=7, end_line=7)],
        )
        assert "class Marker:  # L7\n" in render_stub(module)

    def test_function_single_line_range(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="noop", start_line=3, end_line=3)],
        )
        assert "def noop():  # L3\n" in render_stub(module)

    def test_class_no_bases(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Plain", start_line=1, end_line=2)],
        )
        assert "class Plain:  # L1-2" in render_stub(module)

    def test_attribute_with_annotation(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Record",
                    start_line=1,
                    end_line=3,
                    attributes=[StubAssignment("name", annotation="str")],
                )
            ],
        )
        assert "    name: str" in render_stub(module)

    def test_method_indented(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Foo",
                    start_line=1,
                    end_line=5,
                    methods=[
                        StubFunction(
                            name="bar",
                            params=[StubParam("self")],
                            start_line=2,
                            end_line=4,
                        )
                    ],
                )
            ],
        )
        output = render_stub(module)
        assert "    def bar(self):  # L2-4" in output

    def test_ends_with_newline(self):
        module = StubModule(rel_path="pkg/mod.py")
        assert render_stub(module).endswith("\n")

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
        module = extract_stub(source, "pkg/cfg.py")
        output = render_stub(module)
        assert "    path: Path" in output
        assert "def path" not in output

    def test_constant_with_value_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="TIMEOUT", value_source="30", start_line=3, end_line=3
                )
            ],
        )
        assert "TIMEOUT = 30  # L3" in render_stub(module)

    def test_constant_annotated_with_value_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="MAX",
                    annotation="int",
                    value_source="3",
                    start_line=4,
                    end_line=4,
                )
            ],
        )
        assert "MAX: int = 3  # L4" in render_stub(module)

    def test_constant_elided_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="BIG", value_source="...", start_line=5, end_line=10
                )
            ],
        )
        assert "BIG = ...  # L5-10" in render_stub(module)

    def test_constant_bare_annotation_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(name="FOO", annotation="int", start_line=2, end_line=2)
            ],
        )
        output = render_stub(module)
        assert "FOO: int  # L2" in output
        assert "FOO: int = " not in output

    def test_type_alias_pep695_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="UserId",
                    value_source="int",
                    is_type_alias=True,
                    start_line=1,
                    end_line=1,
                )
            ],
        )
        assert "type UserId = int  # L1" in render_stub(module)

    def test_unannotated_class_attribute_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Registry",
                    start_line=1,
                    end_line=3,
                    attributes=[StubAssignment("items", value_source="[]")],
                )
            ],
        )
        output = render_stub(module)
        assert "    items = []" in output
        # No line range comment on class attributes.
        assert "items = []  # L" not in output
