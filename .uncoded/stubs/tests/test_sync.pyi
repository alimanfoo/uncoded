# tests/test_sync.py

from uncoded.sync import remove_file, sync_file

class TestSyncFile:  # L4-56

    def test_creates_missing_file(self, tmp_path):  # L5-9
        ...

    def test_creates_parent_directories(self, tmp_path):  # L11-15
        ...

    def test_updates_when_content_differs(self, tmp_path):  # L17-22
        ...

    def test_noop_when_content_matches(self, tmp_path):  # L24-31
        ...

    def test_check_mode_does_not_create_file(self, tmp_path):  # L33-37
        ...

    def test_check_mode_does_not_update_file(self, tmp_path):  # L39-44
        ...

    def test_check_mode_reports_noop_when_clean(self, tmp_path):  # L46-50
        ...

    def test_check_mode_does_not_create_parent_directories(self, tmp_path):  # L52-56
        ...

class TestRemoveFile:  # L59-82

    def test_removes_existing_file(self, tmp_path):  # L60-65
        ...

    def test_noop_when_absent(self, tmp_path):  # L67-70
        ...

    def test_check_mode_does_not_remove(self, tmp_path):  # L72-77
        ...

    def test_check_mode_reports_noop_when_absent(self, tmp_path):  # L79-82
        ...
