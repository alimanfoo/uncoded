from uncoded.docs_map import extract_headings


class TestExtractHeadings:
    def test_empty_text(self):
        assert extract_headings("") == []

    def test_h1_through_h6(self):
        text = "# One\n## Two\n### Three\n#### Four\n##### Five\n###### Six\n"
        assert extract_headings(text) == [
            (1, "One"),
            (2, "Two"),
            (3, "Three"),
            (4, "Four"),
            (5, "Five"),
            (6, "Six"),
        ]

    def test_trailing_hashes_stripped(self):
        assert extract_headings("### Setup ###\n") == [(3, "Setup")]

    def test_trailing_hashes_with_surrounding_spaces_stripped(self):
        assert extract_headings("## Title ## \n") == [(2, "Title")]

    def test_seven_hashes_not_a_heading(self):
        assert extract_headings("####### Too many\n") == []

    def test_no_space_after_hash_not_a_heading(self):
        assert extract_headings("##NoSpace\n") == []

    def test_hash_only_not_a_heading(self):
        # A lone # with no space and no title.
        assert extract_headings("#\n") == []

    def test_empty_title_not_a_heading(self):
        # Trailing-# strip leaves an empty title.
        assert extract_headings("# #\n") == []

    def test_setext_underline_equals_not_a_heading(self):
        assert extract_headings("Title\n=====\n") == []

    def test_setext_underline_dashes_not_a_heading(self):
        assert extract_headings("Other\n-----\n") == []

    def test_backtick_fence_suppresses_headings(self):
        text = "# Before\n```\n# Inside\n```\n# After\n"
        assert extract_headings(text) == [(1, "Before"), (1, "After")]

    def test_tilde_fence_suppresses_headings(self):
        text = "# Before\n~~~\n# Inside\n~~~\n# After\n"
        assert extract_headings(text) == [(1, "Before"), (1, "After")]

    def test_fence_with_info_string(self):
        text = "# Before\n```python\n# Inside\n```\n# After\n"
        assert extract_headings(text) == [(1, "Before"), (1, "After")]

    def test_unclosed_fence_suppresses_rest_of_file(self):
        text = "# Before\n```\n# Never seen\n"
        assert extract_headings(text) == [(1, "Before")]

    def test_tilde_does_not_close_backtick_fence(self):
        text = "# Before\n```\n# Inside\n~~~\n# Still inside\n```\n# After\n"
        assert extract_headings(text) == [(1, "Before"), (1, "After")]

    def test_backtick_does_not_close_tilde_fence(self):
        text = "# Before\n~~~\n# Inside\n```\n# Still inside\n~~~\n# After\n"
        assert extract_headings(text) == [(1, "Before"), (1, "After")]

    def test_preserves_order(self):
        text = "# A\n## B\n# C\n"
        assert extract_headings(text) == [(1, "A"), (2, "B"), (1, "C")]

    def test_title_with_special_chars(self):
        assert extract_headings("## Hello, World!\n") == [(2, "Hello, World!")]

    def test_leading_spaces_not_a_heading(self):
        # The # must be at column 0; leading spaces are not stripped.
        assert extract_headings("  # Indented\n") == []
