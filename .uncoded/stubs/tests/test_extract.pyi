# tests/test_extract.py

import textwrap
from uncoded.extract import extract_module, walk_source

class TestExtractModule:

    def test_classes_and_functions(self):
        ...

    def test_async_functions_and_methods(self):
        ...

    def test_empty_module(self):
        ...

    def test_module_level_constants(self):
        ...

    def test_type_alias_classic(self):
        ...

    def test_type_alias_pep695(self):
        ...

    def test_tuple_unpacking_skipped(self):
        ...

    def test_unannotated_class_variable(self):
        ...

    def test_module_with_only_constants_is_kept(self, tmp_path):
        ...

    def test_annotated_attributes(self):
        ...

    def test_property_classified_as_attribute(self):
        ...

    def test_property_setter_and_deleter_suppressed(self):
        ...

    def test_preserves_source_order(self):
        ...

class TestWalkSource:

    def test_basic_walk(self, tmp_path):
        ...

    def test_nested_subpackage(self, tmp_path):
        ...

    def test_includes_init_with_symbols(self, tmp_path):
        ...

    def test_skips_empty_init(self, tmp_path):
        ...

    def test_skips_syntax_errors(self, tmp_path):
        ...
