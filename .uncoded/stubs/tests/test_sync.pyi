# tests/test_sync.py

from pathlib import Path
from uncoded.sync import remove_file, sync_file

class TestSyncFile:

    def test_creates_missing_file(self, tmp_path):
        ...

    def test_creates_parent_directories(self, tmp_path):
        ...

    def test_updates_when_content_differs(self, tmp_path):
        ...

    def test_noop_when_content_matches(self, tmp_path):
        ...

    def test_check_mode_does_not_create_file(self, tmp_path):
        ...

    def test_check_mode_does_not_update_file(self, tmp_path):
        ...

    def test_check_mode_reports_noop_when_clean(self, tmp_path):
        ...

    def test_check_mode_does_not_create_parent_directories(self, tmp_path):
        ...

class TestRemoveFile:

    def test_removes_existing_file(self, tmp_path):
        ...

    def test_noop_when_absent(self, tmp_path):
        ...

    def test_check_mode_does_not_remove(self, tmp_path):
        ...

    def test_check_mode_reports_noop_when_absent(self, tmp_path):
        ...

class TestSyncFileProjectRootAnchor:

    def test_project_root_anchors_write_independent_of_cwd(self, tmp_path, monkeypatch):
        ...

    def test_project_root_preserves_relative_path_in_message(self, tmp_path, monkeypatch, capsys):
        ...

    def test_absolute_path_makes_project_root_a_no_op(self, tmp_path, monkeypatch):
        ...

class TestRemoveFileProjectRootAnchor:

    def test_project_root_anchors_removal_independent_of_cwd(self, tmp_path, monkeypatch):
        ...
