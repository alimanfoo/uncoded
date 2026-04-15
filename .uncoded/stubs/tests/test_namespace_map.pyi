# tests/test_namespace_map.py

import yaml
from uncoded.extract import ClassInfo, ModuleInfo
from uncoded.namespace_map import build_map, render_map

class TestBuildMap:  # L7-116

    def test_single_file(self):  # L8-23
        ...

    def test_nested_subpackage(self):  # L25-42
        ...

    def test_class_with_methods(self):  # L44-58
        ...

    def test_class_with_attributes_and_methods(self):  # L60-80
        ...

    def test_function_is_none(self):  # L82-89
        ...

    def test_class_with_no_members(self):  # L91-102
        ...

    def test_source_order_preserved(self):  # L104-116
        ...

class TestRenderMap:  # L119-155

    def test_roundtrips_through_yaml(self):  # L120-133
        ...

    def test_preserves_insertion_order(self):  # L135-144
        ...

    def test_null_renders_clean(self):  # L146-155
        ...
