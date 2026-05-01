import textwrap

from uncoded.extract import extract_module, extract_modules, walk_source


class TestExtractModule:
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

        result = extract_module(source, "module.py")

        assert result.rel_path == "module.py"
        assert len(result.classes) == 2
        assert result.classes[0].name == "MyClass"
        assert result.classes[0].methods == ["public_method", "_private_method"]
        assert result.classes[1].name == "_PrivateClass"
        assert result.classes[1].methods == ["method"]
        assert result.functions == ["public_function", "_private_function"]

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

        result = extract_module(source, "async_module.py")

        assert result.functions == ["fetch_data"]
        assert result.classes[0].name == "Client"
        assert result.classes[0].methods == ["connect", "disconnect"]

    def test_empty_module(self):
        result = extract_module("", "empty.py")

        assert result.classes == []
        assert result.functions == []

    def test_module_level_constants(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
            MAX_RETRIES: int = 3
            __version__ = "1.0.0"
        """)

        result = extract_module(source, "const.py")

        assert result.constants == ["TIMEOUT", "MAX_RETRIES", "__version__"]

    def test_type_alias_classic(self):
        source = textwrap.dedent("""\
            from typing import TypeAlias
            UserId: TypeAlias = int
        """)

        result = extract_module(source, "aliases.py")

        assert result.constants == ["UserId"]

    def test_type_alias_pep695(self):
        source = textwrap.dedent("""\
            type UserId = int
            type InternalId = int
        """)

        result = extract_module(source, "aliases.py")

        assert result.constants == ["UserId", "InternalId"]

    def test_tuple_unpacking_skipped(self):
        source = textwrap.dedent("""\
            X, Y = 1, 2
        """)

        result = extract_module(source, "tuple.py")

        assert result.constants == []

    def test_unannotated_class_variable(self):
        source = textwrap.dedent("""\
            class Registry:
                items = []
                _cache = {}
                count: int = 0
        """)

        result = extract_module(source, "reg.py")

        cls = result.classes[0]
        assert cls.attributes == ["items", "_cache", "count"]

    def test_module_with_only_constants_is_kept(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text('__version__ = "1.0"\n')

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/__init__.py" in rel_paths

    def test_annotated_attributes(self):
        source = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Record:
                name: str
                value: int
                _internal: float

                def process(self):
                    pass
        """)

        result = extract_module(source, "record.py")

        cls = result.classes[0]
        assert cls.name == "Record"
        assert cls.attributes == ["name", "value", "_internal"]
        assert cls.methods == ["process"]

    def test_property_classified_as_attribute(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path

                def save(self):
                    pass
        """)

        result = extract_module(source, "config.py")

        cls = result.classes[0]
        assert cls.attributes == ["path"]
        assert cls.methods == ["save"]

    def test_property_setter_and_deleter_suppressed(self):
        source = textwrap.dedent("""\
            class Config:
                @property
                def path(self):
                    return self._path

                @path.setter
                def path(self, value):
                    self._path = value

                @path.deleter
                def path(self):
                    del self._path
        """)

        result = extract_module(source, "config.py")

        cls = result.classes[0]
        assert cls.attributes == ["path"]
        assert cls.methods == []

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

        result = extract_module(source, "ordering.py")

        assert result.functions == ["zebra", "apple"]
        assert result.classes[0].methods == ["omega", "alpha"]


class TestWalkSource:
    def test_basic_walk(self, tmp_path):
        # Simulate repo structure: src/mypackage/...
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "core.py").write_text(
            textwrap.dedent("""\
                class Engine:
                    def run(self):
                        pass

                def start():
                    pass
            """)
        )
        (pkg / "_internal.py").write_text("def helper(): pass\n")
        (pkg / "empty.py").write_text("# nothing here\n")

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/core.py" in rel_paths
        assert "src/mypackage/_internal.py" in rel_paths
        assert any("__init__.py" in p for p in rel_paths) is False
        assert any("empty.py" in p for p in rel_paths) is False

    def test_nested_subpackage(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        sub = pkg / "utils"
        sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (sub / "__init__.py").write_text("")
        (sub / "formatting.py").write_text("def format_output(): pass\n")

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/utils/formatting.py" in rel_paths

    def test_includes_init_with_symbols(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("def create(): pass\n")
        (pkg / "core.py").write_text("def run(): pass\n")

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/__init__.py" in rel_paths
        assert "src/mypackage/core.py" in rel_paths

    def test_skips_empty_init(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "core.py").write_text("def run(): pass\n")

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert not any("__init__.py" in p for p in rel_paths)

    def test_skips_syntax_errors(self, tmp_path, capsys):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "good.py").write_text("def works(): pass\n")
        (pkg / "bad.py").write_text("def broken(:\n")

        modules = walk_source(src, base=tmp_path)

        rel_paths = [m.rel_path for m in modules]
        assert "src/mypackage/good.py" in rel_paths
        assert any("bad.py" in p for p in rel_paths) is False

        # Skipping must be visible — a silent skip means a stale stub
        # for the offending file would never get refreshed and the user
        # would have no breadcrumb to investigate. The warning names the
        # file so they can find it.
        err = capsys.readouterr().err
        assert "warning: skipping src/mypackage/bad.py" in err
        assert "SyntaxError" in err


class TestExtractModules:
    def test_returns_module_info_per_parseable_file(self):
        files = [
            ("def foo(): pass\n", "src/a.py"),
            ("class Bar: pass\n", "src/b.py"),
        ]

        modules = extract_modules(files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py"]
        assert modules[0].functions == ["foo"]
        assert modules[1].classes[0].name == "Bar"

    def test_preserves_source_order(self):
        files = [
            ("def a(): pass\n", "src/a.py"),
            ("def b(): pass\n", "src/b.py"),
            ("def c(): pass\n", "src/c.py"),
        ]

        modules = extract_modules(files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py", "src/c.py"]

    def test_skips_files_with_no_symbols(self):
        files = [
            ("def foo(): pass\n", "src/a.py"),
            ("# nothing here\n", "src/empty.py"),
            ("class Bar: pass\n", "src/b.py"),
        ]

        modules = extract_modules(files)

        assert [m.rel_path for m in modules] == ["src/a.py", "src/b.py"]
