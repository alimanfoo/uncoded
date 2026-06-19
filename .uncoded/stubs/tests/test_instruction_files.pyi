# tests/test_instruction_files.py

import hashlib
from pathlib import Path
from hypothesis import given
from hypothesis.strategies import text as st_text
from uncoded.instruction_files import _CODE_SECTION_BODY, MARKER_DOCS_END, MARKER_DOCS_START, MARKER_END, MARKER_START, MARKER_START_PREFIX, SECTION_CODE, SECTION_DOCS, _apply_section, sync_instruction_file

class TestCodeSection:
    def test_contains_markers(self):
        ...

    def test_markers_in_order(self):
        ...

    def test_ends_with_newline(self):
        ...

class TestDocsSection:
    def test_contains_markers(self):
        ...

    def test_markers_in_order(self):
        ...

    def test_ends_with_newline(self):
        ...

    def test_mentions_docs_yaml(self):
        ...

class TestSyncInstructionFile:
    def test_creates_file_with_code_section(self, tmp_path):
        ...

    def test_appends_code_section_to_existing_file(self, tmp_path):
        ...

    def test_replaces_existing_code_section(self, tmp_path):
        ...

    def test_preserves_content_after_code_section(self, tmp_path):
        ...

    def test_removes_code_section_on_none(self, tmp_path):
        ...

    def test_appends_docs_section(self, tmp_path):
        ...

    def test_removes_docs_section_on_none(self, tmp_path):
        ...

    def test_both_sections_appended_in_order(self, tmp_path):
        ...

    def test_both_sections_replaced_independently(self, tmp_path):
        ...

    def test_code_only_does_not_write_docs_markers(self, tmp_path):
        ...

    def test_docs_only_does_not_write_code_markers(self, tmp_path):
        ...

    def test_idempotent(self, tmp_path):
        ...

    def test_returns_true_on_first_write(self, tmp_path):
        ...

    def test_returns_false_when_clean(self, tmp_path):
        ...

    def test_returns_false_when_both_none_and_file_absent(self, tmp_path):
        ...

    def test_remove_section_absent_is_noop(self, tmp_path):
        ...

class TestSyncInstructionFileCheckMode:
    def test_does_not_create_file(self, tmp_path):
        ...

    def test_does_not_update_existing_file(self, tmp_path):
        ...

    def test_reports_no_change_when_clean(self, tmp_path):
        ...

class TestSyncInstructionFileProjectRootAnchor:
    def test_project_root_anchors_create_independent_of_cwd(self, tmp_path, monkeypatch):
        ...

    def test_project_root_anchors_update_of_existing_file(self, tmp_path, monkeypatch):
        ...

class TestSyncInstructionFileFingerprint:
    def test_reflowed_body_survives_sync(self, tmp_path):
        ...

    def test_reflowed_body_passes_check(self, tmp_path):
        ...

    def test_different_fingerprint_refreshes_section(self, tmp_path):
        ...

    def test_plain_marker_refreshes_once_then_stable(self, tmp_path):
        ...

    def test_prose_mention_of_prefix_before_section_is_ignored(self, tmp_path):
        ...

class TestApplySectionConvergence:
    def test_idempotent(self, t: str) -> None:
        ...

    def test_lines_outside_section_survive(self, t: str) -> None:
        ...

    def test_prose_end_marker_at_line_start_survives(self) -> None:
        ...

    def test_crlf_converges_in_one_pass(self) -> None:
        ...

    def test_duplicate_sections_collapsed_to_one(self) -> None:
        ...

    def test_end_before_start_does_not_loop(self) -> None:
        ...

    def test_lone_start_orphan_section_inserted_before_and_prose_preserved(self) -> None:
        ...

class TestSyncInstructionFileFingerprintDocs:
    def test_reflowed_body_survives_sync(self, tmp_path):
        ...

    def test_reflowed_body_passes_check(self, tmp_path):
        ...

    def test_different_fingerprint_refreshes_section(self, tmp_path):
        ...

    def test_plain_marker_refreshes_once_then_stable(self, tmp_path):
        ...

    def test_prose_mention_of_prefix_before_section_is_ignored(self, tmp_path):
        ...

class TestMarkerStamp:
    def test_marker_start_stamp_derives_from_code_section_body(self) -> None:
        ...
