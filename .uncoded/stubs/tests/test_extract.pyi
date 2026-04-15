# tests/test_extract.py

import textwrap
from uncoded.extract import extract_module, is_public, walk_source

class TestIsPublic:  # L6-20

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

class TestExtractModule:  # L23-152

    def test_classes_and_functions(self):  # L24-50
        ...

    def test_async_functions_and_methods(self):  # L52-69
        ...

    def test_empty_module(self):  # L71-75
        ...

    def test_only_private_symbols(self):  # L77-91
        ...

    def test_annotated_attributes(self):  # L93-112
        ...

    def test_class_with_no_public_members(self):  # L114-131
        ...

    def test_preserves_source_order(self):  # L133-152
        ...

class TestWalkSource:  # L155-246

    def test_basic_walk(self, tmp_path):  # L156-181
        ...

    def test_nested_subpackage(self, tmp_path):  # L183-195
        ...

    def test_skips_private_subdirectory(self, tmp_path):  # L197-207
        ...

    def test_includes_init_with_public_symbols(self, tmp_path):  # L209-220
        ...

    def test_skips_empty_init(self, tmp_path):  # L222-232
        ...

    def test_skips_syntax_errors(self, tmp_path):  # L234-246
        ...
