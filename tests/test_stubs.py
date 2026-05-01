import os
import textwrap

import pytest

from uncoded.stubs import (
    StubAssignment,
    StubClass,
    StubFunction,
    StubModule,
    StubParam,
    build_stubs,
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

    def test_docstring_starting_with_eg_not_truncated(self):
        # Sentence-boundary heuristic requires whitespace+capital after the
        # period, so ``e.g.`` followed by lowercase isn't mistaken for the
        # end of the first sentence.
        source = textwrap.dedent("""\
            def process():
                '''e.g. parse a YAML file. Then validate it.'''
                pass
        """)
        module = extract_stub(source, "pkg/proc.py")
        assert module.functions[0].docstring_excerpt == "e.g. parse a YAML file."

    def test_docstring_starting_with_ie_not_truncated(self):
        source = textwrap.dedent("""\
            def process():
                '''i.e. validate the input. Then proceed.'''
                pass
        """)
        module = extract_stub(source, "pkg/proc.py")
        assert module.functions[0].docstring_excerpt == "i.e. validate the input."

    def test_docstring_starting_with_us_initialism_not_truncated(self):
        # Multi-character initialism with internal periods. The ``e`` after
        # ``U.S.`` is lowercase, so the heuristic skips past the abbreviation
        # and lands on the next capital-after-period.
        source = textwrap.dedent("""\
            def policy():
                '''U.S. economic policy. Then global.'''
                pass
        """)
        module = extract_stub(source, "pkg/policy.py")
        assert module.functions[0].docstring_excerpt == "U.S. economic policy."

    def test_no_docstring(self):
        source = textwrap.dedent("""\
            def silent():
                pass
        """)
        module = extract_stub(source, "pkg/silent.py")
        assert module.functions[0].docstring_excerpt is None

    def test_module_docstring_extracted(self):
        # Module-level docstrings follow the same first-sentence convention
        # as class/function docstrings, so a multi-sentence module docstring
        # is captured as just its leading sentence.
        source = textwrap.dedent("""\
            '''Top-level utility for greetings. Sub-module of pkg.'''

            def hello() -> str:
                pass
        """)
        module = extract_stub(source, "pkg/greet.py")
        assert module.docstring_excerpt == "Top-level utility for greetings."

    def test_module_no_docstring(self):
        source = textwrap.dedent("""\
            def hello() -> str:
                pass
        """)
        module = extract_stub(source, "pkg/greet.py")
        assert module.docstring_excerpt is None

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
        assert "VALUE = 1" in output
        assert "def run():\n    ..." in output
        assert "class Worker:" in output
        assert "    def work(self):" in output
        assert "# L" not in output

    def test_async_function_prefix(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            functions=[StubFunction(name="fetch", is_async=True)],
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
                )
            ],
        )
        output = render_stub(module)
        assert '"""Do the thing."""' in output
        assert '"""Do the thing."""\n    ...' in output

    def test_module_docstring_rendered_at_top(self):
        # The module docstring sits between the path-comment header and
        # the imports block, matching where a real Python module's
        # docstring lives.
        module = StubModule(
            rel_path="pkg/mod.py",
            docstring_excerpt="Greetings utility.",
            imports=["from typing import Final"],
        )
        output = render_stub(module)
        assert output.startswith(
            '# pkg/mod.py\n\n"""Greetings utility."""\n\nfrom typing import Final'
        )

    def test_class_with_bases(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Dog", bases=["Animal"])],
        )
        assert "class Dog(Animal):" in render_stub(module)

    def test_class_no_bases(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            classes=[StubClass(name="Plain")],
        )
        assert "class Plain:" in render_stub(module)

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
        assert "    name: str" in render_stub(module)

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
        assert "    def bar(self):" in output

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
            constants=[StubAssignment(name="TIMEOUT", value_source="30")],
        )
        assert "TIMEOUT = 30" in render_stub(module)

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
        assert "MAX: int = 3" in render_stub(module)

    def test_constant_elided_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="BIG", value_source="...")],
        )
        assert "BIG = ..." in render_stub(module)

    def test_constant_bare_annotation_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[StubAssignment(name="FOO", annotation="int")],
        )
        output = render_stub(module)
        assert "FOO: int" in output
        assert "FOO: int = " not in output

    def test_type_alias_pep695_rendered(self):
        module = StubModule(
            rel_path="pkg/mod.py",
            constants=[
                StubAssignment(
                    name="UserId",
                    value_source="int",
                    is_type_alias=True,
                )
            ],
        )
        assert "type UserId = int" in render_stub(module)

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
        assert "    items = []" in output
        assert "# L" not in output


class TestBuildStubs:
    """build_stubs writes expected stubs and removes orphans for its source root."""

    def _setup(self, tmp_path):
        os.chdir(tmp_path)
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "stubs"
        return src, out

    def test_writes_expected_stubs(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        assert (out / "src" / "foo.pyi").exists()

    def test_removes_orphan_stub_when_source_deleted(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        build_stubs(src, out)
        assert (out / "src" / "bar.pyi").exists()

        (src / "bar.py").unlink()
        build_stubs(src, out)
        assert (out / "src" / "foo.pyi").exists()
        assert not (out / "src" / "bar.pyi").exists()

    def test_removes_orphan_stub_when_source_renamed(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "old_name.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        assert (out / "src" / "old_name.pyi").exists()

        (src / "old_name.py").rename(src / "new_name.py")
        build_stubs(src, out)
        assert (out / "src" / "new_name.pyi").exists()
        assert not (out / "src" / "old_name.pyi").exists()

    def test_prunes_empty_directories(self, tmp_path):
        src, out = self._setup(tmp_path)
        pkg = src / "pkg"
        pkg.mkdir()
        (pkg / "mod.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        assert (out / "src" / "pkg" / "mod.pyi").exists()

        # Remove the whole subpackage; the stub directory should be pruned.
        (pkg / "mod.py").unlink()
        pkg.rmdir()
        build_stubs(src, out)
        assert not (out / "src" / "pkg").exists()

    def test_does_not_touch_other_source_root(self, tmp_path):
        src, out = self._setup(tmp_path)
        tests = tmp_path / "tests"
        tests.mkdir()
        (src / "foo.py").write_text("def hello(): pass\n")
        (tests / "test_foo.py").write_text("def test_hello(): pass\n")

        build_stubs(src, out)
        build_stubs(tests, out)
        assert (out / "src" / "foo.pyi").exists()
        assert (out / "tests" / "test_foo.pyi").exists()

        # Rebuilding only `src` must leave the `tests` stub alone.
        build_stubs(src, out)
        assert (out / "tests" / "test_foo.pyi").exists()

    def test_no_op_when_clean(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        # Second build with no source changes should not error and should
        # leave the stub in place.
        build_stubs(src, out)
        assert (out / "src" / "foo.pyi").exists()

    def test_reports_count_on_first_build(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        assert build_stubs(src, out) == 2

    def test_reports_zero_when_clean(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        assert build_stubs(src, out) == 0


class TestBuildStubsCheckMode:
    """build_stubs with check=True must report changes without mutating the tree."""

    def _setup(self, tmp_path):
        os.chdir(tmp_path)
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "stubs"
        return src, out

    def test_does_not_write_stub_in_check_mode(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        changes = build_stubs(src, out, check=True)
        assert changes == 1
        assert not (out / "src" / "foo.pyi").exists()

    def test_zero_changes_when_clean(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        assert build_stubs(src, out, check=True) == 0

    def test_detects_stale_stub_content(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        build_stubs(src, out)
        # Simulate a source edit that would change the stub.
        (src / "foo.py").write_text("def hello(name: str) -> str: pass\n")
        assert build_stubs(src, out, check=True) == 1

    def test_detects_orphan_stub_without_removing_it(self, tmp_path):
        src, out = self._setup(tmp_path)
        (src / "foo.py").write_text("def hello(): pass\n")
        (src / "bar.py").write_text("def goodbye(): pass\n")
        build_stubs(src, out)
        (src / "bar.py").unlink()
        assert build_stubs(src, out, check=True) == 1
        # Check mode must not mutate the tree — orphan is still there.
        assert (out / "src" / "bar.pyi").exists()
