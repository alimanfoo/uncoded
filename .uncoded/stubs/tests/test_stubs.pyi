# tests/test_stubs.py

import textwrap
import pytest
from uncoded.stubs import StubClass, StubFunction, StubModule, StubParam, extract_stub, render_stub

class TestExtractStub:  # L15-171

    def test_simple_function(self):  # L16-30
        ...

    def test_function_no_annotations(self):  # L32-40
        ...

    def test_async_function(self):  # L42-50
        ...

    def test_private_function_excluded(self):  # L52-59
        ...

    def test_class_with_attributes_and_methods(self):  # L61-83
        ...

    def test_class_line_range(self):  # L85-101
        ...

    def test_class_with_bases(self):  # L103-109
        ...

    def test_class_no_bases(self):  # L111-117
        ...

    def test_docstring_first_sentence_only(self):  # L119-126
        ...

    def test_no_docstring(self):  # L128-134
        ...

    def test_kwargs_and_varargs(self):  # L136-144
        ...

    def test_imports_collected(self):  # L146-156
        ...

    def test_syntax_error_raises(self):  # L158-160
        ...

    def test_source_order_preserved(self):  # L162-171
        ...

class TestRenderStub:  # L174-291

    def test_header_contains_path(self):  # L175-177
        ...

    def test_imports_rendered(self):  # L179-185
        ...

    def test_function_line_range(self):  # L187-195
        ...

    def test_async_function_prefix(self):  # L197-204
        ...

    def test_function_with_annotations(self):  # L206-219
        ...

    def test_docstring_excerpt_rendered(self):  # L221-235
        ...

    def test_class_with_bases(self):  # L237-244
        ...

    def test_class_no_bases(self):  # L246-251
        ...

    def test_attribute_with_annotation(self):  # L253-265
        ...

    def test_method_indented(self):  # L267-287
        ...

    def test_ends_with_newline(self):  # L289-291
        ...
