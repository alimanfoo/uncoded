import textwrap
from pathlib import Path

import pytest

from uncoded.extract import iter_source_files
from uncoded.stubs import (
    StubAssignment,
    StubClass,
    StubFunction,
    StubModule,
    StubParam,
    _write_stubs,
    build_stubs,
    extract_stub,
    render_stub,
)


def _setup(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "stubs"
    return src, out


def _build(source_root, out, tmp_path, *, check=False):
    return build_stubs(
        files=list(iter_source_files(source_root, project_root=tmp_path)),
        source_root=source_root,
        output_dir=out,
        project_root=tmp_path,
        check=check,
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
        module = extract_stub(source, "pkg/animals.py")
        assert module.classes[0].bases == ["Animal", "Domestic"]

    def test_class_no_bases(self):
        source = textwrap.dedent("""\
            class Plain:
                pass
        """)
        module = extract_stub(source, "pkg/plain.py")
        assert module.classes[0].bases == []

    @pytest.mark.parametrize(
        "source,expected",
        [
            pytest.param(
                "def f(x): pass\n",
                [StubParam("x")],
                id="regular_positional_bare",
            ),
            pytest.param(
                "def f(x: str): pass\n",
                [StubParam("x", "str")],
                id="regular_positional_annotated",
            ),
            pytest.param(
                "def f(x: int = 0): pass\n",
                [StubParam("x", "int")],
                id="defaults_dropped_positional",
            ),
            pytest.param(
                "def f(*args): pass\n",
                [StubParam("*args")],
                id="varargs_bare",
            ),
            pytest.param(
                "def f(*args: str): pass\n",
                [StubParam("*args", "str")],
                id="varargs_annotated",
            ),
            pytest.param(
                "def f(**kwargs): pass\n",
                [StubParam("**kwargs")],
                id="kwargs_bare",
            ),
            pytest.param(
                "def f(**kwargs: int): pass\n",
                [StubParam("**kwargs", "int")],
                id="kwargs_annotated",
            ),
            pytest.param(
                "def f(x, /): pass\n",
                [StubParam("x"), StubParam("/")],
                id="posonly_bare",
            ),
            pytest.param(
                "def f(x: str, /): pass\n",
                [StubParam("x", "str"), StubParam("/")],
                id="posonly_annotated",
            ),
            pytest.param(
                "def f(*, x): pass\n",
                [StubParam("*"), StubParam("x")],
                id="kwonly_bare",
            ),
            pytest.param(
                "def f(*, x: str): pass\n",
                [StubParam("*"), StubParam("x", "str")],
                id="kwonly_annotated",
            ),
            pytest.param(
                "def f(*, x: int = 0): pass\n",
                [StubParam("*"), StubParam("x", "int")],
                id="defaults_dropped_kwonly",
            ),
            pytest.param(
                "def f(*args, x): pass\n",
                [StubParam("*args"), StubParam("x")],
                id="vararg_with_kwonly",
            ),
            pytest.param(
                "def f(*args, **kwargs): pass\n",
                [StubParam("*args"), StubParam("**kwargs")],
                id="vararg_with_kwarg",
            ),
        ],
    )
    def test_extract_params_covers_input_kind(self, source, expected):
        module = extract_stub(source, "pkg/f.py")
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
        assert c.is_pep695_alias is False

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
        assert c.is_pep695_alias is False

    def test_type_alias_pep695(self):
        source = textwrap.dedent("""\
            type UserId = int
        """)
        module = extract_stub(source, "pkg/mod.py")
        c = module.constants[0]
        assert c.name == "UserId"
        assert c.is_pep695_alias is True
        assert c.value_source == "int"

    def test_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            X, Y = 1, 2
        """)
        module = extract_stub(source, "pkg/mod.py")
        assert module.constants == []

    def test_ann_assign_non_name_target_skipped(self):
        source = "obj.x: int = 1\n"
        module = extract_stub(source, "pkg/mod.py")
        assert module.constants == []

    def test_class_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            class C:
                a, b = 1, 2
        """)
        module = extract_stub(source, "pkg/mod.py")
        assert module.classes[0].attributes == []

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
        assert "import os\nfrom pathlib import Path\n" in output

    def test_rendered_stub_has_no_line_range_comments(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="VALUE", value_source="1")],
            functions=[StubFunction(name="run")],
            classes=[
                StubClass(
                    name="Worker",
                    methods=[
                        StubFunction(
                            name="work",
                            params=[StubParam("self")],
                        )
                    ],
                )
            ],
        )
        output = render_stub(module)
        assert "VALUE = 1\n" in output
        assert "def run():\n    ...\n" in output
        assert "class Worker:\n    def work(self):\n        ...\n" in output
        assert "# L" not in output

    def test_async_function_prefix(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="fetch", is_async=True)],
        )
        assert "async def fetch():\n    ...\n" in render_stub(module)

    @pytest.mark.parametrize(
        "params,expected",
        [
            pytest.param(
                [StubParam("x")],
                "def f(x):",
                id="regular_positional_bare",
            ),
            pytest.param(
                [StubParam("x", "str")],
                "def f(x: str):",
                id="regular_positional_annotated",
            ),
            pytest.param(
                [StubParam("*args")],
                "def f(*args):",
                id="varargs_bare",
            ),
            pytest.param(
                [StubParam("*args", "str")],
                "def f(*args: str):",
                id="varargs_annotated",
            ),
            pytest.param(
                [StubParam("**kwargs")],
                "def f(**kwargs):",
                id="kwargs_bare",
            ),
            pytest.param(
                [StubParam("**kwargs", "int")],
                "def f(**kwargs: int):",
                id="kwargs_annotated",
            ),
            pytest.param(
                [StubParam("/")],
                "def f(/):",
                id="positional_only_separator",
            ),
            pytest.param(
                [StubParam("*")],
                "def f(*):",
                id="keyword_only_separator",
            ),
        ],
    )
    def test_render_param_covers_input_kind(self, params, expected):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="f", params=params)],
        )
        assert expected in render_stub(module)

    def test_return_annotation_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="f", return_annotation="str")],
        )
        assert "def f() -> str:" in render_stub(module)

    def test_class_with_bases(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Dog", bases=["Animal"])],
        )
        assert "class Dog(Animal):\n    ...\n" in render_stub(module)

    def test_class_with_no_members_renders_body(self):
        # A class with no attributes and no methods needs an explicit
        # body so the rendered stub is valid Python.
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Sentinel")],
        )
        output = render_stub(module)
        assert "class Sentinel:\n    ...\n" in output
        compile(output, "pkg/mod.pyi", "exec")

    def test_attribute_with_annotation(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Record",
                    attributes=[StubAssignment("name", annotation="str")],
                )
            ],
        )
        assert "class Record:\n    name: str\n" in render_stub(module)

    def test_method_indented(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Foo",
                    methods=[
                        StubFunction(
                            name="bar",
                            params=[StubParam("self")],
                        )
                    ],
                )
            ],
        )
        output = render_stub(module)
        assert "class Foo:\n    def bar(self):\n        ...\n" in output

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
        assert "class Config:\n    path: Path\n" in output
        assert "def path" not in output

    def test_constant_with_value_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="TIMEOUT", value_source="30")],
        )
        assert "TIMEOUT = 30\n" in render_stub(module)

    def test_constant_annotated_with_value_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="MAX",
                    annotation="int",
                    value_source="3",
                )
            ],
        )
        assert "MAX: int = 3\n" in render_stub(module)

    def test_constant_elided_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="BIG", value_source="...")],
        )
        assert "BIG = ...\n" in render_stub(module)

    def test_constant_bare_annotation_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="FOO", annotation="int")],
        )
        output = render_stub(module)
        assert "FOO: int\n" in output
        assert "FOO: int = " not in output

    def test_type_alias_pep695_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="UserId",
                    value_source="int",
                    is_pep695_alias=True,
                )
            ],
        )
        assert "type UserId = int\n" in render_stub(module)

    def test_unannotated_class_attribute_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[
                StubClass(
                    name="Registry",
                    attributes=[StubAssignment("items", value_source="[]")],
                )
            ],
        )
        output = render_stub(module)
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
        module = extract_stub(source, "pkg/representative.py")
        output = render_stub(module)
        compile(output, "pkg/representative.pyi", "exec")


class TestBuildStubs:
    """build_stubs writes expected stubs and removes orphans for its source root."""

    def test_writes_expected_stubs(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert (out / "src" / "foo.pyi").exists()

    def test_removes_orphan_stub_when_source_deleted(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        _build(src, out, tmp_path)
        assert (out / "src" / "bar.pyi").exists()

        (src / "bar.py").unlink()
        _build(src, out, tmp_path)
        assert (out / "src" / "foo.pyi").exists()
        assert not (out / "src" / "bar.pyi").exists()

    def test_removes_orphan_stub_when_source_renamed(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "old_name.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert (out / "src" / "old_name.pyi").exists()

        (src / "old_name.py").rename(src / "new_name.py")
        _build(src, out, tmp_path)
        assert (out / "src" / "new_name.pyi").exists()
        assert not (out / "src" / "old_name.pyi").exists()

    def test_prunes_empty_directories(self, tmp_path):
        src, out = _setup(tmp_path)
        pkg = src / "pkg"
        pkg.mkdir()
        (pkg / "mod.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert (out / "src" / "pkg" / "mod.pyi").exists()

        # Remove the whole subpackage; the stub directory should be pruned.
        (pkg / "mod.py").unlink()
        pkg.rmdir()
        _build(src, out, tmp_path)
        assert not (out / "src" / "pkg").exists()

    def test_does_not_touch_other_source_root(self, tmp_path):
        src, out = _setup(tmp_path)
        tests = tmp_path / "tests"
        tests.mkdir()
        (src / "foo.py").write_text("def hello(): pass\n")
        (tests / "test_foo.py").write_text("def test_hello(): pass\n")

        _build(src, out, tmp_path)
        _build(tests, out, tmp_path)
        assert (out / "src" / "foo.pyi").exists()
        assert (out / "tests" / "test_foo.pyi").exists()

        # Rebuilding only `src` must leave the `tests` stub alone.
        _build(src, out, tmp_path)
        assert (out / "tests" / "test_foo.pyi").exists()

    def test_no_op_when_clean(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        # Second build with no source changes should not error and should
        # leave the stub in place.
        _build(src, out, tmp_path)
        assert (out / "src" / "foo.pyi").exists()

    def test_reports_count_on_first_build(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        assert _build(src, out, tmp_path) == 2

    def test_reports_zero_when_clean(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert _build(src, out, tmp_path) == 0

    def test_skips_module_with_no_symbols(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "empty.py").write_text('"""Only a module docstring."""\n')
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert not (out / "src" / "empty.pyi").exists()
        assert (out / "src" / "foo.pyi").exists()


class TestBuildStubsCheckMode:
    """build_stubs with check=True must report changes without mutating the tree."""

    def test_does_not_write_stub_in_check_mode(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        changes = _build(src, out, tmp_path, check=True)
        assert changes == 1
        assert not (out / "src" / "foo.pyi").exists()

    def test_zero_changes_when_clean(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        assert _build(src, out, tmp_path, check=True) == 0

    def test_detects_stale_stub_content(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        _build(src, out, tmp_path)
        # Simulate a source edit that would change the stub.
        (src / "foo.py").write_text("def hello(name: str) -> str: pass\n")
        assert _build(src, out, tmp_path, check=True) == 1

    def test_detects_orphan_stub_without_removing_it(self, tmp_path):
        src, out = _setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        _build(src, out, tmp_path)
        (src / "bar.py").unlink()
        assert _build(src, out, tmp_path, check=True) == 1
        # Check mode must not mutate the tree — orphan is still there.
        assert (out / "src" / "bar.pyi").exists()


class TestWriteStubs:
    def test_writes_stubs(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "stubs"
        stubs = {Path("src/foo.pyi"): "# stub\n"}

        changes = _write_stubs(
            stubs=stubs,
            source_root=src,
            output_dir=out,
            project_root=tmp_path,
            check=False,
        )

        assert changes == 1
        assert (out / "src" / "foo.pyi").read_text() == "# stub\n"

    def test_check_mode_does_not_write(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "stubs"
        stubs = {Path("src/foo.pyi"): "# stub\n"}

        changes = _write_stubs(
            stubs=stubs,
            source_root=src,
            output_dir=out,
            project_root=tmp_path,
            check=True,
        )

        assert changes == 1
        assert not (out / "src" / "foo.pyi").exists()

    def test_prunes_orphan_stubs(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "stubs"
        (out / "src" / "pkg").mkdir(parents=True)
        (out / "src" / "pkg" / "orphan.pyi").write_text("# stale\n")

        changes = _write_stubs(
            stubs={},
            source_root=src,
            output_dir=out,
            project_root=tmp_path,
            check=False,
        )

        assert changes == 1
        assert not (out / "src" / "pkg" / "orphan.pyi").exists()
        assert not (out / "src" / "pkg").exists()
        assert (out / "src").exists()

    def test_project_root_anchors_writes_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        # output_dir is project-relative; project_root anchors the actual
        # writes under tmp_path even when cwd is elsewhere.
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)
        src = tmp_path / "src"
        src.mkdir()
        out = Path("stubs")
        stubs = {Path("src/foo.pyi"): "# stub\n"}

        changes = _write_stubs(
            stubs=stubs,
            source_root=src,
            output_dir=out,
            project_root=tmp_path,
            check=False,
        )

        assert changes == 1
        assert (tmp_path / out / "src" / "foo.pyi").read_text() == "# stub\n"
        assert not (sub / out / "src" / "foo.pyi").exists()

    def test_project_root_anchors_orphan_pruning_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)
        src = tmp_path / "src"
        src.mkdir()
        out = Path("stubs")
        (tmp_path / out / "src" / "pkg").mkdir(parents=True)
        (tmp_path / out / "src" / "pkg" / "orphan.pyi").write_text("# stale\n")

        changes = _write_stubs(
            stubs={},
            source_root=src,
            output_dir=out,
            project_root=tmp_path,
            check=False,
        )

        assert changes == 1
        assert not (tmp_path / out / "src" / "pkg" / "orphan.pyi").exists()
        assert not (tmp_path / out / "src" / "pkg").exists()

    def test_source_root_outside_project_root_skips_cleanup(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        out = project / "stubs"

        changes = _write_stubs(
            stubs={},
            source_root=outside,
            output_dir=out,
            project_root=project,
            check=False,
        )

        assert changes == 0
