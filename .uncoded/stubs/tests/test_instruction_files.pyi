# tests/test_instruction_files.py

from uncoded.instruction_files import MARKER_END, MARKER_START, generate_section, sync_instruction_file

class TestGenerateSection:

    def test_contains_markers(self):
        ...

    def test_markers_in_order(self):
        ...

    def test_ends_with_newline(self):
        ...

class TestSyncInstructionFile:

    def test_creates_file_if_missing(self, tmp_path):
        ...

    def test_appends_to_existing_file(self, tmp_path):
        ...

    def test_replaces_existing_section(self, tmp_path):
        ...

    def test_preserves_content_after_section(self, tmp_path):
        ...

    def test_idempotent(self, tmp_path):
        ...

    def test_returns_true_on_first_write(self, tmp_path):
        ...

    def test_returns_false_when_clean(self, tmp_path):
        ...

class TestSyncInstructionFileCheckMode:

    def test_does_not_create_file(self, tmp_path):
        ...

    def test_does_not_update_existing_file(self, tmp_path):
        ...

    def test_reports_no_change_when_clean(self, tmp_path):
        ...
