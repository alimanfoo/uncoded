import textwrap

import yaml

from uncoded.extract import extract_python_file
from uncoded.namespace_map import HEADER, build_map, render_map


def _map(*, sources):
    """Build the namespace map of the Python files that map rel_path to source."""
    return build_map(
        python_files=[
            extract_python_file(source=textwrap.dedent(source), rel_path=rel_path)
            for rel_path, source in sources.items()
        ]
    )


class TestBuildMap:
    def test_single_file(self):
        result = _map(
            sources={
                "src/mypackage/core.py": """\
                class Engine:
                    def run(self): ...
                    def stop(self): ...

                def start(): ...
            """
            }
        )

        core = result["src/"]["mypackage/"]["core.py"]
        assert core["Engine"] == {"run": None, "stop": None}
        assert core["start"] is None

    def test_nested_subpackage(self):
        result = _map(
            sources={
                "src/mypackage/core.py": "def start(): ...\n",
                "src/mypackage/utils/helpers.py": "def format_output(): ...\n",
            }
        )

        pkg = result["src/"]["mypackage/"]
        assert pkg["core.py"] == {"start": None}
        assert pkg["utils/"]["helpers.py"] == {"format_output": None}

    def test_class_with_attributes_and_methods(self):
        result = _map(
            sources={
                "src/pkg/models.py": """\
                class User:
                    def save(self): ...

                    name: str

                    @property
                    def email(self) -> str: ...
            """
            }
        )

        members = result["src/"]["pkg/"]["models.py"]["User"]
        assert list(members) == ["name", "email", "save"]
        assert all(value is None for value in members.values())

    def test_class_with_no_members(self):
        result = _map(sources={"src/pkg/types.py": "class Marker: ...\n"})

        assert result["src/"]["pkg/"]["types.py"]["Marker"] is None

    def test_lists_assignments_then_classes_then_functions(self):
        result = _map(
            sources={
                "src/pkg/settings.py": """\
                def load(): ...
                class Settings: ...
                TIMEOUT = 30
                type Ids = list[int]
                MAX_RETRIES: int
            """
            }
        )

        file_entry = result["src/"]["pkg/"]["settings.py"]
        assert list(file_entry) == ["TIMEOUT", "Ids", "MAX_RETRIES", "Settings", "load"]

    def test_name_defined_twice_is_listed_once(self):
        result = _map(
            sources={
                "src/shapes.py": """\
                class Shape:
                    def scale(self): ...
                    def scale(self, factor): ...

                def area(): ...
                def area(width): ...
            """
            }
        )

        assert result["src/"]["shapes.py"] == {"Shape": {"scale": None}, "area": None}

    def test_keeps_the_kind_of_the_later_definition(self):
        result = _map(
            sources={
                "redefined.py": """\
                class Shape:
                    def scale(self): ...

                Shape = 1

                def area(): ...

                class area:
                    def compute(self): ...

                class Point:
                    x = 0

                class Point:
                    y = 0
            """
            }
        )

        assert result["redefined.py"] == {
            "Shape": None,
            "area": {"compute": None},
            "Point": {"y": None},
        }


class TestRenderMap:
    def test_roundtrips_through_yaml(self):
        namespace = _map(
            sources={"src/pkg/core.py": "class Engine:\n    def run(self): ...\n"}
        )
        output = render_map(namespace=namespace)

        assert yaml.safe_load(output) == namespace

    def test_preserves_insertion_order(self):
        namespace = _map(
            sources={
                "src/pkg/zebra.py": "def z_func(): ...\n",
                "src/pkg/alpha.py": "def a_func(): ...\n",
            }
        )
        output = render_map(namespace=namespace)

        assert output.index("zebra.py") < output.index("alpha.py")

    def test_function_renders_without_null(self):
        output = render_map(
            namespace=_map(sources={"src/pkg/utils.py": "def compute(): ...\n"})
        )

        assert "compute:" in output
        assert "null" not in output

    def test_header_appears_at_top(self):
        output = render_map(
            namespace=_map(sources={"src/pkg/utils.py": "def compute(): ...\n"})
        )
        assert output.startswith(HEADER)
        # Header must precede any non-comment YAML content.
        assert output.index(HEADER) < output.index("src/")

    def test_header_mentions_stub_pointer(self):
        # The header's job is partly to tell a cold-start agent where to find
        # signatures and types. Lock in that pointer.
        output = render_map(namespace=build_map(python_files=[]))
        assert ".uncoded/stubs/" in output
