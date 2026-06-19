import hashlib
from pathlib import Path

from hypothesis import given
from hypothesis.strategies import text as st_text

from uncoded.instruction_files import (
    _CODE_SECTION_BODY,
    MARKER_DOCS_END,
    MARKER_DOCS_START,
    MARKER_END,
    MARKER_START,
    MARKER_START_PREFIX,
    SECTION_CODE,
    SECTION_DOCS,
    _apply_section,
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

    def test_prose_mention_of_prefix_before_section_is_ignored(self, tmp_path):
        # A line that contains the marker prefix inside prose (not at column 0)
        # must not be mistaken for the section opener. Only a line that starts
        # at column 0 is a valid opener.
        path = tmp_path / "CLAUDE.md"
        prose = "Use `<!-- uncoded:start` markers to delimit sections.\n\n"
        old_section = f"<!-- uncoded:start -->\nold body\n{MARKER_END}\n"
        path.write_text(f"{prose}{old_section}")
        result = sync_instruction_file(
            path, code_section=SECTION_CODE, docs_section=None, project_root=tmp_path
        )
        # The real section (old plain marker) is replaced; the prose is preserved.
        assert result is True
        content = path.read_text()
        assert "<!-- uncoded:start` markers" in content
        assert "old body" not in content
        assert SECTION_CODE in content


class TestApplySectionConvergence:
    """Property tests and regression cases for _apply_section convergence."""

    @given(st_text())
    def test_idempotent(self, t: str) -> None:
        first = _apply_section(
            t, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        second = _apply_section(
            first, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        assert first == second

    @given(st_text())
    def test_lines_outside_section_survive(self, t: str) -> None:
        input_lines = t.splitlines(keepends=True)
        # Find the managed section range using the same locator as _apply_section.
        section_start = None
        section_end = None
        for i, line in enumerate(input_lines):
            stripped = line.rstrip("\r\n")
            if section_start is None:
                if stripped.startswith(MARKER_START_PREFIX):
                    section_start = i
            else:
                if stripped == MARKER_END:
                    section_end = i
                    break
        result = _apply_section(
            t, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        result_line_contents = {
            ln.rstrip("\r\n") for ln in result.splitlines(keepends=True)
        }
        for i, line in enumerate(input_lines):
            stripped = line.rstrip("\r\n")
            if stripped.startswith(MARKER_START_PREFIX) or stripped == MARKER_END:
                continue  # marker lines may be rewritten
            if (
                section_start is not None
                and section_end is not None
                and section_start <= i <= section_end
            ):
                continue  # body inside managed section is replaced
            if not stripped:
                continue  # blank lines may be absorbed by lstrip
            assert stripped in result_line_contents

    def test_prose_end_marker_at_line_start_survives(self) -> None:
        # An end marker at the start of a line that appears before any start
        # marker is an orphan and must not be deleted.
        orphan_text = f"```\n{MARKER_END}\n```\n"
        result = _apply_section(
            orphan_text,
            MARKER_START,
            MARKER_END,
            SECTION_CODE,
            prefix=MARKER_START_PREFIX,
        )
        assert MARKER_END in result
        # Second pass must not change anything.
        assert (
            _apply_section(
                result,
                MARKER_START,
                MARKER_END,
                SECTION_CODE,
                prefix=MARKER_START_PREFIX,
            )
            == result
        )

    def test_crlf_converges_in_one_pass(self) -> None:
        # A CRLF file is matched on the first sync and does not trigger a second
        # rewrite.
        crlf_section = f"{MARKER_START}\r\nbody line\r\n{MARKER_END}\r\n"
        first = _apply_section(
            crlf_section,
            MARKER_START,
            MARKER_END,
            SECTION_CODE,
            prefix=MARKER_START_PREFIX,
        )
        second = _apply_section(
            first, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        assert first == second

    def test_duplicate_sections_collapsed_to_one(self) -> None:
        two_sections = f"{SECTION_CODE}{SECTION_CODE}"
        result = _apply_section(
            two_sections,
            MARKER_START,
            MARKER_END,
            SECTION_CODE,
            prefix=MARKER_START_PREFIX,
        )
        assert result.count(MARKER_START) == 1
        assert result.count(MARKER_END) == 1

    def test_end_before_start_does_not_loop(self) -> None:
        # An end marker appearing before any start marker must not cause the
        # section to be appended on every sync.
        text = f"{MARKER_END}\nsome prose\n{SECTION_CODE}"
        first = _apply_section(
            text, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        second = _apply_section(
            first, MARKER_START, MARKER_END, SECTION_CODE, prefix=MARKER_START_PREFIX
        )
        assert first == second

    def test_lone_start_orphan_section_inserted_before_and_prose_preserved(
        self,
    ) -> None:
        # A start marker with no matching end marker is a lone orphan. The
        # canonical section is inserted before it so the next sync sees the
        # section first; the orphan line is preserved (prose not deleted).
        orphan_start = "<!-- uncoded:start -->\nsome prose after\n"
        result = _apply_section(
            orphan_start,
            MARKER_START,
            MARKER_END,
            SECTION_CODE,
            prefix=MARKER_START_PREFIX,
        )
        assert SECTION_CODE in result
        assert "<!-- uncoded:start -->" in result
        assert "some prose after" in result
        # Result must be stable on a second pass.
        assert (
            _apply_section(
                result,
                MARKER_START,
                MARKER_END,
                SECTION_CODE,
                prefix=MARKER_START_PREFIX,
            )
            == result
        )


class TestSyncInstructionFileFingerprintDocs:
    def test_reflowed_body_survives_sync(self, tmp_path):
        # A formatter's reflow of the docs-section body does not trigger a
        # rewrite — the opening marker fingerprint still matches.
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        path.write_text(f"{MARKER_DOCS_START}\nReflowed body.\n{MARKER_DOCS_END}\n")
        result = sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert result is False
        assert "Reflowed body." in path.read_text()

    def test_reflowed_body_passes_check(self, tmp_path):
        # check mode also reports no change when the docs opening marker matches.
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        path.write_text(f"{MARKER_DOCS_START}\nReflowed body.\n{MARKER_DOCS_END}\n")
        result = sync_instruction_file(
            path,
            code_section=None,
            docs_section=SECTION_DOCS,
            project_root=tmp_path,
            check=True,
        )
        assert result is False

    def test_different_fingerprint_refreshes_section(self, tmp_path):
        # A docs section from an older uncoded version (different fingerprint)
        # is replaced with the current canonical section.
        path = tmp_path / "CLAUDE.md"
        old_marker = "<!-- uncoded:docs:start sha256=deadbeef -->"
        path.write_text(f"{old_marker}\nOld wording.\n{MARKER_DOCS_END}\n")
        result = sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert result is True
        content = path.read_text()
        assert SECTION_DOCS in content
        assert "Old wording." not in content

    def test_plain_marker_refreshes_once_then_stable(self, tmp_path):
        # An old plain docs marker (no fingerprint) is refreshed on the first
        # sync after upgrading uncoded, then stays stable.
        path = tmp_path / "CLAUDE.md"
        path.write_text(f"<!-- uncoded:docs:start -->\nold body\n{MARKER_DOCS_END}\n")
        result = sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert result is True
        assert SECTION_DOCS in path.read_text()
        result = sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert result is False

    def test_prose_mention_of_prefix_before_section_is_ignored(self, tmp_path):
        # A line that contains the docs marker prefix inside prose (not at
        # column 0) must not be mistaken for the section opener.
        path = tmp_path / "CLAUDE.md"
        prose = "Use `<!-- uncoded:docs:start` markers to delimit sections.\n\n"
        old_section = f"<!-- uncoded:docs:start -->\nold body\n{MARKER_DOCS_END}\n"
        path.write_text(f"{prose}{old_section}")
        result = sync_instruction_file(
            path, code_section=None, docs_section=SECTION_DOCS, project_root=tmp_path
        )
        assert result is True
        content = path.read_text()
        assert "<!-- uncoded:docs:start` markers" in content
        assert "old body" not in content
        assert SECTION_DOCS in content


class TestMarkerStamp:
    def test_marker_start_stamp_derives_from_code_section_body(self) -> None:
        expected = hashlib.sha256(_CODE_SECTION_BODY.encode()).hexdigest()[:8]
        assert MARKER_START.endswith(expected + " -->")
