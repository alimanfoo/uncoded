from pathlib import Path

import yaml

from uncoded.docs_map import (
    DOCS_HEADER,
    build_docs_map,
    extract_headings,
    read_doc_files,
    render_docs_map,
)


class TestExtractHeadings:
    def test_empty_text(self):
        assert extract_headings(text="") == []

    def test_h1_through_h6(self):
        text = "# One\n## Two\n### Three\n#### Four\n##### Five\n###### Six\n"
        assert extract_headings(text=text) == [
            (1, "One"),
            (2, "Two"),
            (3, "Three"),
            (4, "Four"),
            (5, "Five"),
            (6, "Six"),
        ]

    def test_trailing_hashes_stripped(self):
        assert extract_headings(text="### Setup ###\n") == [(3, "Setup")]

    def test_trailing_hashes_with_surrounding_spaces_stripped(self):
        assert extract_headings(text="## Title ## \n") == [(2, "Title")]

    def test_trailing_hashes_multiple_stripped(self):
        assert extract_headings(text="## Done ###\n") == [(2, "Done")]

    def test_hash_attached_to_word_preserved(self):
        # C# — the # is not preceded by whitespace, so it is not a closing
        # sequence and must be kept in the title.
        assert extract_headings(text="## Using C#\n") == [(2, "Using C#")]

    def test_multiple_hashes_attached_to_words_preserved(self):
        assert extract_headings(text="## C# vs F#\n") == [(2, "C# vs F#")]

    def test_hash_attached_to_word_with_closing_sequence(self):
        # Closing sequence (space + ##) is stripped; C# in the middle is kept.
        assert extract_headings(text="## C# intro ##\n") == [(2, "C# intro")]

    def test_seven_hashes_not_a_heading(self):
        assert extract_headings(text="####### Too many\n") == []

    def test_no_space_after_hash_not_a_heading(self):
        assert extract_headings(text="##NoSpace\n") == []

    def test_hash_only_not_a_heading(self):
        # A lone # with no space and no title.
        assert extract_headings(text="#\n") == []

    def test_empty_title_not_a_heading(self):
        # Trailing-# strip leaves an empty title.
        assert extract_headings(text="# #\n") == []

    def test_setext_underline_equals_not_a_heading(self):
        assert extract_headings(text="Title\n=====\n") == []

    def test_setext_underline_dashes_not_a_heading(self):
        assert extract_headings(text="Other\n-----\n") == []

    def test_backtick_fence_suppresses_headings(self):
        text = "# Before\n```\n# Inside\n```\n# After\n"
        assert extract_headings(text=text) == [(1, "Before"), (1, "After")]

    def test_tilde_fence_suppresses_headings(self):
        text = "# Before\n~~~\n# Inside\n~~~\n# After\n"
        assert extract_headings(text=text) == [(1, "Before"), (1, "After")]

    def test_fence_with_info_string(self):
        text = "# Before\n```python\n# Inside\n```\n# After\n"
        assert extract_headings(text=text) == [(1, "Before"), (1, "After")]

    def test_unclosed_fence_suppresses_rest_of_file(self):
        text = "# Before\n```\n# Never seen\n"
        assert extract_headings(text=text) == [(1, "Before")]

    def test_tilde_does_not_close_backtick_fence(self):
        text = "# Before\n```\n# Inside\n~~~\n# Still inside\n```\n# After\n"
        assert extract_headings(text=text) == [(1, "Before"), (1, "After")]

    def test_backtick_does_not_close_tilde_fence(self):
        text = "# Before\n~~~\n# Inside\n```\n# Still inside\n~~~\n# After\n"
        assert extract_headings(text=text) == [(1, "Before"), (1, "After")]

    def test_preserves_order(self):
        text = "# A\n## B\n# C\n"
        assert extract_headings(text=text) == [(1, "A"), (2, "B"), (1, "C")]

    def test_title_with_special_chars(self):
        assert extract_headings(text="## Hello, World!\n") == [(2, "Hello, World!")]

    def test_leading_spaces_not_a_heading(self):
        # The # must be at column 0; leading spaces are not stripped.
        assert extract_headings(text="  # Indented\n") == []


class TestReadDocFiles:
    def test_single_file_root(self, *, tmp_path):
        md = tmp_path / "README.md"
        md.write_text("# Hello\n", encoding="utf-8")
        results, _skipped = read_doc_files(doc_root=md, project_directory=tmp_path)
        assert len(results) == 1
        text, rel = results[0]
        assert text == "# Hello\n"
        assert rel == "README.md"

    def test_directory_walk_reads_md_files(self, *, tmp_path):
        (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        assert len(results) == 2

    def test_directory_walk_sorted(self, *, tmp_path):
        (tmp_path / "z.md").write_text("z", encoding="utf-8")
        (tmp_path / "a.md").write_text("a", encoding="utf-8")
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        names = [Path(r[1]).name for r in results]
        assert names == ["a.md", "z.md"]

    def test_directory_excludes_non_md(self, *, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("some text", encoding="utf-8")
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        assert len(results) == 1
        assert results[0][1] == "guide.md"

    def test_directory_nested_subdir(self, *, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "guide.md").write_text("# Guide\n", encoding="utf-8")
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        assert len(results) == 1
        assert results[0][1] == "docs/guide.md"

    def test_empty_directory_reads_nothing(self, *, tmp_path):
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        assert results == []

    def test_rel_path_is_relative_to_project_directory(self, *, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("", encoding="utf-8")
        results, _skipped = read_doc_files(doc_root=docs, project_directory=tmp_path)
        assert results[0][1] == "docs/a.md"

    def test_skips_non_utf8_file(self, *, tmp_path):
        # A file with invalid UTF-8 bytes must be skipped; other files in the
        # same directory must still be read.
        guide = tmp_path / "docs" / "guide"
        guide.mkdir(parents=True)
        (guide / "good.md").write_text("# Good\n", encoding="utf-8")
        (guide / "bad.md").write_bytes(b"\xff\xfe not utf-8")
        results, skipped = read_doc_files(
            doc_root=tmp_path / "docs", project_directory=tmp_path
        )
        assert len(results) == 1
        assert results[0][1] == "docs/guide/good.md"
        assert [s.path for s in skipped] == ["docs/guide/bad.md"]

    def test_skips_unreadable_file_with_reason(self, *, tmp_path):
        # A directory whose name ends in .md cannot be read as a file. The
        # reason leaves out the error's own copy of the path, which would use
        # the system's separator.
        (tmp_path / "docs" / "notes.md").mkdir(parents=True)
        results, skipped = read_doc_files(
            doc_root=tmp_path / "docs", project_directory=tmp_path
        )
        assert results == []
        assert [s.path for s in skipped] == ["docs/notes.md"]
        assert skipped[0].reason
        assert str(tmp_path) not in skipped[0].reason

    def test_single_file_root_unreadable_is_skipped(self, *, tmp_path):
        # When the single-file root itself is unreadable, nothing is read and
        # the root is skipped under its project-relative path.
        (tmp_path / "docs").mkdir()
        bad = tmp_path / "docs" / "bad.md"
        bad.write_bytes(b"\xff\xfe not utf-8")
        results, skipped = read_doc_files(doc_root=bad, project_directory=tmp_path)
        assert results == []
        assert [s.path for s in skipped] == ["docs/bad.md"]

    def test_bom_prefixed_file_heading_appears(self, *, tmp_path):
        # A UTF-8 BOM before the first heading must not suppress it.
        bom = b"\xef\xbb\xbf"
        (tmp_path / "guide.md").write_bytes(bom + b"# Guide\n")
        results, _skipped = read_doc_files(
            doc_root=tmp_path, project_directory=tmp_path
        )
        assert len(results) == 1
        text, _rel = results[0]
        assert extract_headings(text=text) == [(1, "Guide")]


class TestBuildDocsMap:
    def test_empty_files(self):
        assert build_docs_map(files=[]) == {}

    def test_headingless_file_maps_to_null(self, *, tmp_path):
        result = build_docs_map(files=[("no headings here", "notes.md")])
        assert result == {"notes.md": None}

    def test_single_heading(self):
        result = build_docs_map(files=[("# Setup\n", "guide.md")])
        assert result == {"guide.md": {"Setup": None}}

    def test_nesting_parent_child(self):
        text = "# Install\n## Steps\n"
        result = build_docs_map(files=[(text, "guide.md")])
        assert result == {"guide.md": {"Install": {"Steps": None}}}

    def test_level_skip_attaches_to_nearest_shallower(self):
        # H2 → H4: H4 should nest under H2 (nearest shallower).
        text = "## Config\n#### Advanced\n"
        result = build_docs_map(files=[(text, "ref.md")])
        assert result == {"ref.md": {"Config": {"Advanced": None}}}

    def test_heading_returns_to_same_level(self):
        # H1 → H2 → H1: second H1 is a sibling of the first.
        text = "# A\n## Sub\n# B\n"
        result = build_docs_map(files=[(text, "f.md")])
        assert result == {"f.md": {"A": {"Sub": None}, "B": None}}

    def test_heading_not_starting_at_h1(self):
        # File starts at H2 — lands at file root.
        text = "## Setup\n### Detail\n"
        result = build_docs_map(files=[(text, "f.md")])
        assert result == {"f.md": {"Setup": {"Detail": None}}}

    def test_duplicate_sibling_disambiguation(self):
        text = "## Setup\n## Setup\n"
        result = build_docs_map(files=[(text, "f.md")])
        assert result == {"f.md": {"Setup": None, "Setup (2)": None}}

    def test_duplicate_increments_past_existing_suffix(self):
        # Three duplicates: Setup, Setup (2), Setup (3).
        text = "## Setup\n## Setup\n## Setup\n"
        result = build_docs_map(files=[(text, "f.md")])
        assert result == {"f.md": {"Setup": None, "Setup (2)": None, "Setup (3)": None}}

    def test_directory_structure_dir_key_has_trailing_slash(self):
        result = build_docs_map(files=[("# Guide\n", "docs/guide.md")])
        assert result == {"docs/": {"guide.md": {"Guide": None}}}

    def test_two_files_in_same_directory(self):
        files = [
            ("# A\n", "docs/a.md"),
            ("# B\n", "docs/b.md"),
        ]
        result = build_docs_map(files=files)
        assert result == {"docs/": {"a.md": {"A": None}, "b.md": {"B": None}}}

    def test_multiple_files_flat(self):
        files = [
            ("# Intro\n", "intro.md"),
            ("# API\n", "api.md"),
        ]
        result = build_docs_map(files=files)
        assert result == {"intro.md": {"Intro": None}, "api.md": {"API": None}}


class TestRenderDocsMap:
    def test_header_present(self):
        output = render_docs_map(mapping={})
        assert output.startswith(DOCS_HEADER)

    def test_roundtrips_through_yaml(self):
        files = [("# Setup\n## Config\n", "guide.md")]
        m = build_docs_map(files=files)
        output = render_docs_map(mapping=m)
        parsed = yaml.safe_load(output)
        assert parsed == m

    def test_headingless_file_renders_without_null(self):
        # Null leaves must render as "key:" not "key: null".
        files = [("no headings", "notes.md")]
        output = render_docs_map(mapping=build_docs_map(files=files))
        assert "notes.md: null" not in output
        assert "notes.md:" in output
