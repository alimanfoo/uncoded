from pathlib import Path

from uncoded.instruction_files import (
    MARKER_DOCS_END,
    MARKER_DOCS_START,
    MARKER_END,
    MARKER_START,
    SECTION_CODE,
    SECTION_DOCS,
    sync_instruction_file,
)


class TestCodeSection:
    def test_contains_markers(self):
        assert MARKER_START in SECTION_CODE
        assert MARKER_END in SECTION_CODE

    def test_markers_in_order(self):
        assert SECTION_CODE.index(MARKER_START) < SECTION_CODE.index(MARKER_END)

    def test_ends_with_newline(self):
        assert SECTION_CODE.endswith("\n")


class TestDocsSection:
    def test_contains_markers(self):
        assert MARKER_DOCS_START in SECTION_DOCS
        assert MARKER_DOCS_END in SECTION_DOCS

    def test_markers_in_order(self):
        start_pos = SECTION_DOCS.index(MARKER_DOCS_START)
        end_pos = SECTION_DOCS.index(MARKER_DOCS_END)
        assert start_pos < end_pos

    def test_ends_with_newline(self):
        assert SECTION_DOCS.endswith("\n")

    def test_mentions_docs_yaml(self):
        assert "docs.yaml" in SECTION_DOCS


class TestSyncInstructionFile:
    def test_creates_file_with_code_section(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert path.exists()
        assert SECTION_CODE in path.read_text()

    def test_appends_code_section_to_existing_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text("# My Project\n\nSome content.\n")
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        content = path.read_text()
        assert "# My Project" in content
        assert SECTION_CODE in content

    def test_replaces_existing_code_section(self, tmp_path):
        # An old plain marker (no fingerprint) is replaced with the current section.
        path = tmp_path / "CLAUDE.md"
        old_section = f"<!-- uncoded:start -->\nold content\n{MARKER_END}\n"
        path.write_text(f"# My Project\n\n{old_section}")
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        content = path.read_text()
        assert "old content" not in content
        assert SECTION_CODE in content
        assert "# My Project" in content

    def test_preserves_content_after_code_section(self, tmp_path):
        # Content after the old section is preserved when replacing.
        path = tmp_path / "CLAUDE.md"
        old_section = f"<!-- uncoded:start -->\nold\n{MARKER_END}\n"
        path.write_text(f"{old_section}\n## Other section\n")
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert "## Other section" in path.read_text()

    def test_removes_code_section_on_none(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text(f"# Header\n\n{SECTION_CODE}\n## Footer\n")
        sync_instruction_file(
            path, code_section=None, docs_section=None, project_root=tmp_path
        )
        content = path.read_text()
        assert MARKER_START not in content
        assert "# Header" in content
        assert "## Footer" in content

    def test_appends_docs_section(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert path.exists()
        assert SECTION_DOCS in path.read_text()

    def test_removes_docs_section_on_none(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text(f"# Header\n\n{SECTION_DOCS}\n## Footer\n")
        sync_instruction_file(
            path, code_section=None, docs_section=None, project_root=tmp_path
        )
        content = path.read_text()
        assert MARKER_DOCS_START not in content
        assert "# Header" in content

    def test_both_sections_appended_in_order(self, tmp_path):
        # On a fresh file, code section appears before docs section.
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=SECTION_DOCS,
            project_root=tmp_path,
        )
        content = path.read_text()
        assert SECTION_CODE in content
        assert SECTION_DOCS in content
        assert content.index(MARKER_START) < content.index(MARKER_DOCS_START)

    def test_both_sections_replaced_independently(self, tmp_path):
        # Old plain markers for both sections are each replaced without
        # disturbing the other.
        path = tmp_path / "CLAUDE.md"
        path.write_text(
            f"# Title\n\n<!-- uncoded:start -->\nold code\n{MARKER_END}\n\n"
            f"<!-- uncoded:docs:start -->\nold docs\n{MARKER_DOCS_END}\n"
        )
        sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=SECTION_DOCS,
            project_root=tmp_path,
        )
        content = path.read_text()
        assert "old code" not in content
        assert "old docs" not in content
        assert SECTION_CODE in content
        assert SECTION_DOCS in content

    def test_code_only_does_not_write_docs_markers(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert MARKER_DOCS_START not in path.read_text()

    def test_docs_only_does_not_write_code_markers(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert MARKER_START not in path.read_text()

    def test_idempotent(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        first = path.read_text()
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert path.read_text() == first

    def test_returns_true_on_first_write(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        assert (
            sync_instruction_file(
                path,
                code_section=SECTION_CODE,
                docs_section=None,
                project_root=tmp_path,
            )
            is True
        )

    def test_returns_false_when_clean(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert (
            sync_instruction_file(
                path,
                code_section=SECTION_CODE,
                docs_section=None,
                project_root=tmp_path,
            )
            is False
        )

    def test_returns_false_when_both_none_and_file_absent(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        assert (
            sync_instruction_file(
                path, code_section=None, docs_section=None, project_root=tmp_path
            )
            is False
        )
        assert not path.exists()

    def test_remove_section_absent_is_noop(self, tmp_path):
        # Removing a section that isn't there produces no write.
        path = tmp_path / "CLAUDE.md"
        path.write_text("# Just prose\n")
        result = sync_instruction_file(
            path, code_section=None, docs_section=None, project_root=tmp_path
        )
        assert result is False
        assert path.read_text() == "# Just prose\n"


class TestSyncInstructionFileCheckMode:
    def test_does_not_create_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        changed = sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
            check=True,
        )
        assert changed is True
        assert not path.exists()

    def test_does_not_update_existing_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text("# My Project\n\nSome content.\n")
        original = path.read_text()
        changed = sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
            check=True,
        )
        assert changed is True
        assert path.read_text() == original

    def test_reports_no_change_when_clean(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        changed = sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
            check=True,
        )
        assert changed is False


class TestSyncInstructionFileProjectRootAnchor:
    def test_project_root_anchors_create_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("CLAUDE.md")
        changed = sync_instruction_file(
            rel,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
        )
        assert changed is True
        assert (tmp_path / rel).exists()
        assert SECTION_CODE in (tmp_path / rel).read_text()
        assert not (sub / rel).exists()

    def test_project_root_anchors_update_of_existing_file(self, tmp_path, monkeypatch):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("CLAUDE.md")
        (tmp_path / rel).write_text("# My Project\n\nSome content.\n")

        changed = sync_instruction_file(
            rel,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
        )
        assert changed is True
        content = (tmp_path / rel).read_text()
        assert "# My Project" in content
        assert SECTION_CODE in content


class TestSyncInstructionFileFingerprint:
    def test_reflowed_body_survives_sync(self, tmp_path):
        # Within a version, a formatter's reflow of the section body does
        # not trigger a rewrite — the opening marker fingerprint still matches.
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        # Simulate a markdown formatter reflowing the body between the markers.
        path.write_text(f"{MARKER_START}\nReflowed body.\n{MARKER_END}\n")
        result = sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert result is False
        assert "Reflowed body." in path.read_text()

    def test_reflowed_body_passes_check(self, tmp_path):
        # check mode also reports no change when the opening marker matches.
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        path.write_text(f"{MARKER_START}\nReflowed body.\n{MARKER_END}\n")
        result = sync_instruction_file(
            path,
            code_section=SECTION_CODE,
            docs_section=None,
            project_root=tmp_path,
            check=True,
        )
        assert result is False

    def test_different_fingerprint_refreshes_section(self, tmp_path):
        # A section from an older uncoded version (different fingerprint)
        # is replaced with the current canonical section.
        path = tmp_path / "CLAUDE.md"
        old_marker = "<!-- uncoded:start sha256=deadbeef -->"
        path.write_text(f"{old_marker}\nOld wording.\n{MARKER_END}\n")
        result = sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert result is True
        content = path.read_text()
        assert SECTION_CODE in content
        assert "Old wording." not in content

    def test_plain_marker_refreshes_once_then_stable(self, tmp_path):
        # An old plain marker (no fingerprint) is refreshed on the first
        # sync after upgrading uncoded, then stays stable.
        path = tmp_path / "CLAUDE.md"
        path.write_text(f"<!-- uncoded:start -->\nold body\n{MARKER_END}\n")
        result = sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert result is True
        assert SECTION_CODE in path.read_text()
        result = sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        assert result is False
