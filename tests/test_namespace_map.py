import yaml

from uncoded.extract import ClassInfo, ModuleInfo
from uncoded.namespace_map import build_map, render_map


class TestBuildMap:
    def test_single_file(self):
        modules = [
            ModuleInfo(
                rel_path="src/mypackage/core.py",
                classes=[ClassInfo(name="Engine", methods=["run", "stop"])],
                functions=["start"],
            ),
        ]

        result = build_map(modules)

        assert "src/" in result
        assert "mypackage/" in result["src/"]
        core = result["src/"]["mypackage/"]["core.py"]
        assert core["Engine"] == {"run": None, "stop": None}
        assert core["start"] is None

    def test_nested_subpackage(self):
        modules = [
            ModuleInfo(
                rel_path="src/mypackage/core.py", classes=[], functions=["start"]
            ),
            ModuleInfo(
                rel_path="src/mypackage/utils/helpers.py",
                classes=[],
                functions=["format_output"],
            ),
        ]

        result = build_map(modules)

        pkg = result["src/"]["mypackage/"]
        assert "utils/" in pkg
        assert "helpers.py" in pkg["utils/"]
        assert pkg["utils/"]["helpers.py"]["format_output"] is None

    def test_class_with_methods(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/models.py",
                classes=[ClassInfo(name="User", methods=["save", "delete"])],
                functions=[],
            ),
        ]

        result = build_map(modules)

        assert result["src/"]["pkg/"]["models.py"]["User"] == {
            "save": None,
            "delete": None,
        }

    def test_class_with_attributes_and_methods(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/models.py",
                classes=[
                    ClassInfo(
                        name="User",
                        attributes=["name", "email"],
                        methods=["save"],
                    )
                ],
                functions=[],
            ),
        ]

        result = build_map(modules)

        members = result["src/"]["pkg/"]["models.py"]["User"]
        assert members == {"name": None, "email": None, "save": None}
        # Attributes come before methods
        assert list(members.keys()) == ["name", "email", "save"]

    def test_function_is_none(self):
        modules = [
            ModuleInfo(rel_path="src/pkg/utils.py", classes=[], functions=["compute"]),
        ]

        result = build_map(modules)

        assert result["src/"]["pkg/"]["utils.py"]["compute"] is None

    def test_class_with_no_members(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/types.py",
                classes=[ClassInfo(name="Marker", methods=[])],
                functions=[],
            ),
        ]

        result = build_map(modules)

        assert result["src/"]["pkg/"]["types.py"]["Marker"] is None

    def test_source_order_preserved(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/mixed.py",
                classes=[ClassInfo(name="Alpha", methods=["run"])],
                functions=["zebra", "apple"],
            ),
        ]

        result = build_map(modules)
        keys = list(result["src/"]["pkg/"]["mixed.py"].keys())

        assert keys == ["Alpha", "zebra", "apple"]

    def test_module_level_constants(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/settings.py",
                constants=["TIMEOUT", "MAX_RETRIES"],
                classes=[],
                functions=[],
            ),
        ]

        result = build_map(modules)
        file_entry = result["src/"]["pkg/"]["settings.py"]

        assert file_entry == {"TIMEOUT": None, "MAX_RETRIES": None}

    def test_constants_precede_classes_and_functions(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/mod.py",
                constants=["VERSION"],
                classes=[ClassInfo(name="Foo")],
                functions=["run"],
            ),
        ]

        result = build_map(modules)
        keys = list(result["src/"]["pkg/"]["mod.py"].keys())

        assert keys == ["VERSION", "Foo", "run"]


class TestRenderMap:
    def test_roundtrips_through_yaml(self):
        modules = [
            ModuleInfo(
                rel_path="src/pkg/core.py",
                classes=[ClassInfo(name="Engine", methods=["run"])],
                functions=["start"],
            ),
        ]

        namespace = build_map(modules)
        output = render_map(namespace)

        parsed = yaml.safe_load(output)
        assert parsed == namespace

    def test_preserves_insertion_order(self):
        modules = [
            ModuleInfo(rel_path="src/pkg/zebra.py", classes=[], functions=["z_func"]),
            ModuleInfo(rel_path="src/pkg/alpha.py", classes=[], functions=["a_func"]),
        ]

        namespace = build_map(modules)
        output = render_map(namespace)

        assert output.index("zebra.py") < output.index("alpha.py")

    def test_null_renders_clean(self):
        modules = [
            ModuleInfo(rel_path="src/pkg/utils.py", classes=[], functions=["compute"]),
        ]

        namespace = build_map(modules)
        output = render_map(namespace)

        assert "compute:" in output
        assert "null" not in output
