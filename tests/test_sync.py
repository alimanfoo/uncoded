from pathlib import Path

from uncoded.sync import remove_file, sync_file


class TestSyncFile:
    def test_creates_missing_file(self, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(path, "hello", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "deep" / "out.txt"
        changed = sync_file(path, "hello", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "hello"

    def test_updates_when_content_differs(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old", encoding="utf-8")
        changed = sync_file(path, "new", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "new"

    def test_noop_when_content_matches(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same", encoding="utf-8")
        mtime_before = path.stat().st_mtime_ns
        changed = sync_file(path, "same", project_root=tmp_path)
        assert changed is False
        # No write happened — mtime should not have been bumped.
        assert path.stat().st_mtime_ns == mtime_before

    def test_check_mode_does_not_create_file(self, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(path, "hello", project_root=tmp_path, check=True)
        assert changed is True
        assert not path.exists()

    def test_check_mode_does_not_update_file(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old", encoding="utf-8")
        changed = sync_file(path, "new", project_root=tmp_path, check=True)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "old"

    def test_check_mode_reports_noop_when_clean(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same", encoding="utf-8")
        changed = sync_file(path, "same", project_root=tmp_path, check=True)
        assert changed is False

    def test_check_mode_does_not_create_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "out.txt"
        changed = sync_file(path, "hello", project_root=tmp_path, check=True)
        assert changed is True
        assert not path.parent.exists()


class TestRemoveFile:
    def test_removes_existing_file(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data", encoding="utf-8")
        changed = remove_file(path, project_root=tmp_path)
        assert changed is True
        assert not path.exists()

    def test_noop_when_absent(self, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path, project_root=tmp_path)
        assert changed is False

    def test_check_mode_does_not_remove(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data", encoding="utf-8")
        changed = remove_file(path, project_root=tmp_path, check=True)
        assert changed is True
        assert path.exists()

    def test_check_mode_reports_noop_when_absent(self, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path, project_root=tmp_path, check=True)
        assert changed is False


class TestSyncFileProjectRootAnchor:
    def test_project_root_anchors_write_independent_of_cwd(self, tmp_path, monkeypatch):
        # path is project-relative; project_root anchors I/O at tmp_path
        # even when cwd is elsewhere.
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        changed = sync_file(rel, "hello", project_root=tmp_path)

        assert changed is True
        assert (tmp_path / rel).read_text(encoding="utf-8") == "hello"
        # No write under cwd.
        assert not (sub / rel).exists()

    def test_project_root_preserves_relative_path_in_message(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        rel = Path("out.txt")
        sync_file(rel, "hello", project_root=tmp_path)
        out = capsys.readouterr().out
        # Display stays project-relative; absolute path does not leak in.
        assert f"Wrote {rel}" in out
        assert str(tmp_path) not in out


class TestRemoveFileProjectRootAnchor:
    def test_project_root_anchors_removal_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        target = tmp_path / rel
        target.parent.mkdir(parents=True)
        target.write_text("data", encoding="utf-8")

        changed = remove_file(rel, project_root=tmp_path)
        assert changed is True
        assert not target.exists()
