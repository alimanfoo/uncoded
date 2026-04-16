import textwrap

from uncoded.extract import extract_module, is_public, walk_source


class TestIsPublic:
    def test_public_name(self):
        assert is_public("foo") is True

    def test_class_name(self):
        assert is_public("MyClass") is True

    def test_private_name(self):
        assert is_public("_foo") is False

    def test_dunder_name(self):
        assert is_public("__init__") is False

    def test_name_mangled(self):
        assert is_public("__foo") is False

    def test_dunder_all_is_public(self):
        assert is_public("__all__") is True

    def test_dunder_version_is_public(self):
        assert is_public("__version__") is True


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
        assert len(result.classes) == 1
        assert result.classes[0].name == "MyClass"
        assert result.classes[0].methods == ["public_method"]
        assert result.functions == ["public_function"]

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

    def test_only_private_symbols(self):
        source = textwrap.dedent("""\
            _CONSTANT = 42

            class _Internal:
                pass

            def _helper():
                pass
        """)

        result = extract_module(source, "private.py")

        assert result.classes == []
        assert result.functions == []
        assert result.constants == []

    def test_module_level_constants(self):
        source = textwrap.dedent("""\
            TIMEOUT = 30
            MAX_RETRIES: int = 3
            _PRIVATE = 1
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
            type _PrivateId = int
        """)

        result = extract_module(source, "aliases.py")

        assert result.constants == ["UserId"]

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
        assert cls.attributes == ["items", "count"]

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
        assert cls.attributes == ["name", "value"]
        assert cls.methods == ["process"]

    def test_class_with_no_public_members(self):
        source = textwrap.dedent("""\
            class Config:
                _value = 10

                def __init__(self):
                    pass

                def _setup(self):
                    pass
        """)

        result = extract_module(source, "config.py")

        assert len(result.classes) == 1
        assert result.classes[0].name == "Config"
        assert result.classes[0].attributes == []
        assert result.classes[0].methods == []

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
        assert any("__init__.py" in p for p in rel_paths) is False
        assert any("_internal.py" in p for p in rel_paths) is False
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

    def test_skips_private_subdirectory(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "mypackage"
        private_sub = pkg / "_vendor"
        private_sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (private_sub / "lib.py").write_text("def vendored(): pass\n")

        modules = walk_source(src, base=tmp_path)

        assert modules == []

    def test_includes_init_with_public_symbols(self, tmp_path):
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

    def test_skips_syntax_errors(self, tmp_path):
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
