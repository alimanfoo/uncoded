# tests/test_body.py

import ast
import textwrap
from unittest import mock
import pytest
from uncoded.body import resolve_body
from uncoded.resolver import NamePath, SymbolNotFound, UnsupportedNamePath, resolve_ast_node, resolve_name_position

class TestResolveBodyTopLevel:
    def test_function_without_decorators(self, tmp_path):
        ...

    def test_function_with_decorators(self, tmp_path):
        ...

    def test_async_function(self, tmp_path):
        ...

    def test_class_whole_body(self, tmp_path):
        ...

    def test_module_constant_annotated(self, tmp_path):
        ...

    def test_module_constant_unannotated(self, tmp_path):
        ...

    def test_pep695_type_alias(self, tmp_path):
        ...

    def test_overload_returns_last_definition(self, tmp_path):
        ...

    def test_scans_past_non_matching_constant(self, tmp_path):
        ...

    def test_not_found_raises_body_not_found(self, tmp_path):
        ...

    def test_file_not_found_propagates(self, tmp_path):
        ...

    def test_syntax_error_propagates(self, tmp_path):
        ...

    def test_reads_latin1_declared_file(self, tmp_path):
        ...

class TestResolveBodyClassMember:
    def test_method(self, tmp_path):
        ...

    def test_property_returns_getter_body(self, tmp_path):
        ...

    def test_class_attribute_annotated(self, tmp_path):
        ...

    def test_class_attribute_unannotated(self, tmp_path):
        ...

    def test_scans_past_non_matching_attribute(self, tmp_path):
        ...

    def test_skips_non_function_nodes_in_class(self, tmp_path):
        ...

    def test_shadowed_class_member_found_in_last_definition(self, tmp_path):
        ...

    def test_shadowed_class_member_not_found_in_last_definition(self, tmp_path):
        ...

    def test_not_found_in_class(self, tmp_path):
        ...

class TestUnsupportedNamePath:
    SUPPORTED_SHAPES = ("'name'", "'Class/member'")

    def _assert_raises(self, name_path):
        ...

    def test_three_segment_path(self):
        ...

    def test_nested_class_shape(self):
        ...

    def test_empty_leading_segment(self):
        ...

    def test_empty_trailing_segment(self):
        ...

    def test_empty_middle_segment(self):
        ...

class TestResolveAstNode:
    def test_returns_function_def_for_top_level_function(self, tmp_path):
        ...

    def test_returns_method_node_for_class_member(self, tmp_path):
        ...

    def test_raises_body_not_found(self, tmp_path):
        ...

    def test_raises_unsupported_name_path(self):
        ...

    def test_file_not_found_propagates(self, tmp_path):
        ...

    def test_syntax_error_propagates(self, tmp_path):
        ...

class TestResolveNamePosition:
    def test_function(self, tmp_path):
        ...

    def test_function_decorator_does_not_shift_line(self, tmp_path):
        ...

    def test_async_function(self, tmp_path):
        ...

    def test_class(self, tmp_path):
        ...

    def test_annotated_assignment(self, tmp_path):
        ...

    def test_unannotated_assignment(self, tmp_path):
        ...

    def test_type_alias(self, tmp_path):
        ...

    def test_class_method(self, tmp_path):
        ...

    def test_unexpected_node_type_raises_unsupported_name_path(self, tmp_path):
        ...

class TestResolveBodyByteIdentical:
    def test_exact_source_returned(self, tmp_path):
        ...
