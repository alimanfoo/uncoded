from pathlib import Path

import yaml

from uncoded.docs_map import (
    DOCS_HEADER,
    build_docs_map,
    extract_headings,
    iter_doc_files,
    render_docs_map,
)


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

    def test_trailing_hashes_multiple_stripped(self):
        assert extract_headings("## Done ###\n") == [(2, "Done")]

    def test_hash_attached_to_word_preserved(self):
        # C# — the # is not preceded by whitespace, so it is not a closing
        # sequence and must be kept in the title.
        assert extract_headings("## Using C#\n") == [(2, "Using C#")]

    def test_multiple_hashes_attached_to_words_preserved(self):
        assert extract_headings("## C# vs F#\n") == [(2, "C# vs F#")]

    def test_hash_attached_to_word_with_closing_sequence(self):
        # Closing sequence (space + ##) is stripped; C# in the middle is kept.
        assert extract_headings("## C# intro ##\n") == [(2, "C# intro")]

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


class TestIterDocFiles:
    def test_single_file_root(self, tmp_path):
        md = tmp_path / "README.md"
        md.write_text("# Hello\n", encoding="utf-8")
        results = list(iter_doc_files(md, tmp_path))
        assert len(results) == 1
        text, rel = results[0]
        assert text == "# Hello\n"
        assert rel == Path("README.md")

    def test_directory_walk_yields_md_files(self, tmp_path):
        (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
        results = list(iter_doc_files(tmp_path, tmp_path))
        assert len(results) == 2

    def test_directory_walk_sorted(self, tmp_path):
        (tmp_path / "z.md").write_text("z", encoding="utf-8")
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        results = list(iter_doc_files(tmp_path, tmp_path))
        names = [r[1].name for r in results]
        assert names == ["a.md", "z.md"]

    def test_directory_excludes_non_md(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("some text", encoding="utf-8")
        results = list(iter_doc_files(tmp_path, tmp_path))
        assert len(results) == 1
        assert results[0][1] == Path("guide.md")

    def test_directory_nested_subdir(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("# Guide\n", encoding="utf-8")
        results = list(iter_doc_files(tmp_path, tmp_path))
        assert len(results) == 1
        assert results[0][1] == Path("docs/guide.md")

    def test_empty_directory_yields_nothing(self, tmp_path):
        results = list(iter_doc_files(tmp_path, tmp_path))
        assert results == []

    def test_rel_path_is_relative_to_project_root(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("", encoding="utf-8")
        results = list(iter_doc_files(docs, tmp_path))
        assert results[0][1] == Path("docs/a.md")

    def test_skips_non_utf8_file_with_warning(self, tmp_path, capsys):
        # A file with invalid UTF-8 bytes must be skipped with a warning;
        # other files in the same directory must still yield.
        (tmp_path / "good.md").write_text("# Good\n", encoding="utf-8")
        (tmp_path / "bad.md").write_bytes(b"\xff\xfe not utf-8")
        results = list(iter_doc_files(tmp_path, tmp_path))
        assert len(results) == 1
        assert results[0][1].name == "good.md"
        err = capsys.readouterr().err
        assert "warning: skipping" in err
        assert "bad.md" in err

    def test_single_file_root_unreadable_yields_nothing(self, tmp_path, capsys):
        # When the single-file root itself is unreadable, the iterator yields
        # nothing and emits a warning.
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe not utf-8")
        results = list(iter_doc_files(bad, tmp_path))
        assert results == []
        err = capsys.readouterr().err
        assert "warning: skipping" in err
        assert "bad.md" in err


class TestBuildDocsMap:
    def test_empty_files(self):
        assert build_docs_map([]) == {}

    def test_headingless_file_maps_to_null(self, tmp_path):
        result = build_docs_map([("no headings here", Path("notes.md"))])
        assert result == {"notes.md": None}

    def test_single_heading(self):
        result = build_docs_map([("# Setup\n", Path("guide.md"))])
        assert result == {"guide.md": {"Setup": None}}

    def test_nesting_parent_child(self):
        text = "# Install\n## Steps\n"
        result = build_docs_map([(text, Path("guide.md"))])
        assert result == {"guide.md": {"Install": {"Steps": None}}}

    def test_level_skip_attaches_to_nearest_shallower(self):
        # H2 → H4: H4 should nest under H2 (nearest shallower).
        text = "## Config\n#### Advanced\n"
        result = build_docs_map([(text, Path("ref.md"))])
        assert result == {"ref.md": {"Config": {"Advanced": None}}}

    def test_heading_returns_to_same_level(self):
        # H1 → H2 → H1: second H1 is a sibling of the first.
        text = "# A\n## Sub\n# B\n"
        result = build_docs_map([(text, Path("f.md"))])
        assert result == {"f.md": {"A": {"Sub": None}, "B": None}}

    def test_heading_not_starting_at_h1(self):
        # File starts at H2 — lands at file root.
        text = "## Setup\n### Detail\n"
        result = build_docs_map([(text, Path("f.md"))])
        assert result == {"f.md": {"Setup": {"Detail": None}}}

    def test_duplicate_sibling_disambiguation(self):
        text = "## Setup\n## Setup\n"
        result = build_docs_map([(text, Path("f.md"))])
        assert result == {"f.md": {"Setup": None, "Setup (2)": None}}

    def test_duplicate_increments_past_existing_suffix(self):
        # Three duplicates: Setup, Setup (2), Setup (3).
        text = "## Setup\n## Setup\n## Setup\n"
        result = build_docs_map([(text, Path("f.md"))])
        assert result == {"f.md": {"Setup": None, "Setup (2)": None, "Setup (3)": None}}

    def test_directory_structure_dir_key_has_trailing_slash(self):
        result = build_docs_map([("# Guide\n", Path("docs/guide.md"))])
        assert result == {"docs/": {"guide.md": {"Guide": None}}}

    def test_two_files_in_same_directory(self):
        files = [
            ("# A\n", Path("docs/a.md")),
            ("# B\n", Path("docs/b.md")),
        ]
        result = build_docs_map(files)
        assert result == {"docs/": {"a.md": {"A": None}, "b.md": {"B": None}}}

    def test_multiple_files_flat(self):
        files = [
            ("# Intro\n", Path("intro.md")),
            ("# API\n", Path("api.md")),
        ]
        result = build_docs_map(files)
        assert result == {"intro.md": {"Intro": None}, "api.md": {"API": None}}


class TestRenderDocsMap:
    def test_header_present(self):
        output = render_docs_map({})
        assert output.startswith(DOCS_HEADER)

    def test_yaml_parseable(self):
        files = [("# Setup\n## Config\n", Path("guide.md"))]
        m = build_docs_map(files)
        output = render_docs_map(m)
        parsed = yaml.safe_load(output)
        assert parsed == m

    def test_null_renders_clean(self):
        # Null leaves must render as "key:" not "key: null".
        files = [("no headings", Path("notes.md"))]
        output = render_docs_map(build_docs_map(files))
        assert "notes.md: null" not in output
        assert "notes.md:" in output
