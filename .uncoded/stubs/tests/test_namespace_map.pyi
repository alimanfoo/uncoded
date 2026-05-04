# tests/test_namespace_map.py

import yaml
from uncoded.extract import ClassInfo, ModuleInfo
from uncoded.namespace_map import HEADER, build_map, render_map

class TestBuildMap:

    def test_single_file(self):
        ...

    def test_nested_subpackage(self):
        ...

    def test_class_with_methods(self):
        ...

    def test_class_with_attributes_and_methods(self):
        ...

    def test_function_is_none(self):
        ...

    def test_class_with_no_members(self):
        ...

    def test_class_and_function_insertion_order_preserved(self):
        ...

    def test_module_level_constants(self):
        ...

    def test_constants_precede_classes_and_functions(self):
        ...

class TestRenderMap:

    def test_roundtrips_through_yaml(self):
        ...

    def test_preserves_insertion_order(self):
        ...

    def test_null_renders_clean(self):
        ...

    def test_header_appears_at_top(self):
        ...

    def test_header_mentions_stub_pointer(self):
        ...

    def test_header_does_not_break_yaml_parse(self):
        ...
