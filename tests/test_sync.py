from pathlib import Path

from uncoded.sync import remove_file, sync_file


class TestSyncFile:
    def test_creates_missing_file(self, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(path, "hello")
        assert changed is True
        assert path.read_text() == "hello"

    def test_creates_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "deep" / "out.txt"
        changed = sync_file(path, "hello")
        assert changed is True
        assert path.read_text() == "hello"

    def test_updates_when_content_differs(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old")
        changed = sync_file(path, "new")
        assert changed is True
        assert path.read_text() == "new"

    def test_noop_when_content_matches(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same")
        mtime_before = path.stat().st_mtime_ns
        changed = sync_file(path, "same")
        assert changed is False
        # No write happened — mtime should not have been bumped.
        assert path.stat().st_mtime_ns == mtime_before

    def test_check_mode_does_not_create_file(self, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(path, "hello", check=True)
        assert changed is True
        assert not path.exists()

    def test_check_mode_does_not_update_file(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old")
        changed = sync_file(path, "new", check=True)
        assert changed is True
        assert path.read_text() == "old"

    def test_check_mode_reports_noop_when_clean(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same")
        changed = sync_file(path, "same", check=True)
        assert changed is False

    def test_check_mode_does_not_create_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "out.txt"
        changed = sync_file(path, "hello", check=True)
        assert changed is True
        assert not path.parent.exists()


class TestRemoveFile:
    def test_removes_existing_file(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data")
        changed = remove_file(path)
        assert changed is True
        assert not path.exists()

    def test_noop_when_absent(self, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path)
        assert changed is False

    def test_check_mode_does_not_remove(self, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data")
        changed = remove_file(path, check=True)
        assert changed is True
        assert path.exists()

    def test_check_mode_reports_noop_when_absent(self, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path, check=True)
        assert changed is False


class TestSyncFileRootAnchor:
    def test_root_anchors_write_independent_of_cwd(self, tmp_path, monkeypatch):
        # path is project-relative; root anchors I/O at tmp_path even
        # when cwd is elsewhere.
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        changed = sync_file(rel, "hello", root=tmp_path)

        assert changed is True
        assert (tmp_path / rel).read_text() == "hello"
        # Crucially, no write under cwd.
        assert not (sub / rel).exists()

    def test_root_preserves_relative_path_in_message(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        rel = Path("out.txt")
        sync_file(rel, "hello", root=tmp_path)
        out = capsys.readouterr().out
        # Display stays project-relative; absolute path does not leak in.
        assert f"Wrote {rel}" in out
        assert str(tmp_path) not in out

    def test_absolute_path_makes_root_a_no_op(self, tmp_path, monkeypatch):
        # When path is absolute, root is irrelevant under Path's join
        # semantics — the absolute side wins.
        other = tmp_path / "other"
        other.mkdir()
        target = tmp_path / "out.txt"
        sync_file(target, "hello", root=other)
        assert target.read_text() == "hello"


class TestRemoveFileRootAnchor:
    def test_root_anchors_removal_independent_of_cwd(self, tmp_path, monkeypatch):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        target = tmp_path / rel
        target.parent.mkdir(parents=True)
        target.write_text("data")

        changed = remove_file(rel, root=tmp_path)
        assert changed is True
        assert not target.exists()
