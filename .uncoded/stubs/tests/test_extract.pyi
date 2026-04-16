# tests/test_extract.py

import textwrap
from uncoded.extract import extract_module, is_public, walk_source

class TestIsPublic:  # L6-26

    def test_public_name(self):  # L7-8
        ...

    def test_class_name(self):  # L10-11
        ...

    def test_private_name(self):  # L13-14
        ...

    def test_dunder_name(self):  # L16-17
        ...

    def test_name_mangled(self):  # L19-20
        ...

    def test_dunder_all_is_public(self):  # L22-23
        ...

    def test_dunder_version_is_public(self):  # L25-26
        ...

class TestExtractModule:  # L29-224

    def test_classes_and_functions(self):  # L30-56
        ...

    def test_async_functions_and_methods(self):  # L58-75
        ...

    def test_empty_module(self):  # L77-81
        ...

    def test_only_private_symbols(self):  # L83-98
        ...

    def test_module_level_constants(self):  # L100-110
        ...

    def test_type_alias_classic(self):  # L112-120
        ...

    def test_type_alias_pep695(self):  # L122-130
        ...

    def test_tuple_unpacking_skipped(self):  # L132-139
        ...

    def test_unannotated_class_variable(self):  # L141-152
        ...

    def test_module_with_only_constants_is_kept(self, tmp_path):  # L154-163
        ...

    def test_annotated_attributes(self):  # L165-184
        ...

    def test_class_with_no_public_members(self):  # L186-203
        ...

    def test_preserves_source_order(self):  # L205-224
        ...

class TestWalkSource:  # L227-318

    def test_basic_walk(self, tmp_path):  # L228-253
        ...

    def test_nested_subpackage(self, tmp_path):  # L255-267
        ...

    def test_skips_private_subdirectory(self, tmp_path):  # L269-279
        ...

    def test_includes_init_with_public_symbols(self, tmp_path):  # L281-292
        ...

    def test_skips_empty_init(self, tmp_path):  # L294-304
        ...

    def test_skips_syntax_errors(self, tmp_path):  # L306-318
        ...
