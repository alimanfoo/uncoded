# tests/test_instruction_files.py

from uncoded.instruction_files import MARKER_END, MARKER_START, generate_section, sync_instruction_file

class TestGenerateSection:  # L9-20

    def test_contains_markers(self):  # L10-13
        ...

    def test_markers_in_order(self):  # L15-17
        ...

    def test_ends_with_newline(self):  # L19-20
        ...

class TestSyncInstructionFile:  # L23-70

    def test_creates_file_if_missing(self, tmp_path):  # L24-28
        ...

    def test_appends_to_existing_file(self, tmp_path):  # L30-36
        ...

    def test_replaces_existing_section(self, tmp_path):  # L38-46
        ...

    def test_preserves_content_after_section(self, tmp_path):  # L48-54
        ...

    def test_idempotent(self, tmp_path):  # L56-61
        ...

    def test_returns_true_on_first_write(self, tmp_path):  # L63-65
        ...

    def test_returns_false_when_clean(self, tmp_path):  # L67-70
        ...

class TestSyncInstructionFileCheckMode:  # L73-92

    def test_does_not_create_file(self, tmp_path):  # L74-78
        ...

    def test_does_not_update_existing_file(self, tmp_path):  # L80-86
        ...

    def test_reports_no_change_when_clean(self, tmp_path):  # L88-92
        ...
