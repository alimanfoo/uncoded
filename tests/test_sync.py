from pathlib import Path

import pytest

from uncoded.sync import FileSyncError, remove_file, sync_file


class TestSyncFile:
    def test_creates_missing_file(self, *, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(path=path, content="hello", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "hello"

    def test_creates_parent_directories(self, *, tmp_path):
        path = tmp_path / "nested" / "deep" / "out.txt"
        changed = sync_file(path=path, content="hello", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "hello"

    def test_updates_when_content_differs(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old", encoding="utf-8")
        changed = sync_file(path=path, content="new", project_root=tmp_path)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "new"

    def test_noop_when_content_matches(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same", encoding="utf-8")
        mtime_before = path.stat().st_mtime_ns
        changed = sync_file(path=path, content="same", project_root=tmp_path)
        assert changed is False
        # No write happened — mtime should not have been bumped.
        assert path.stat().st_mtime_ns == mtime_before

    def test_check_mode_does_not_create_file(self, *, tmp_path):
        path = tmp_path / "out.txt"
        changed = sync_file(
            path=path, content="hello", project_root=tmp_path, check=True
        )
        assert changed is True
        assert not path.exists()

    def test_check_mode_does_not_update_file(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("old", encoding="utf-8")
        changed = sync_file(path=path, content="new", project_root=tmp_path, check=True)
        assert changed is True
        assert path.read_text(encoding="utf-8") == "old"

    def test_check_mode_reports_noop_when_clean(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("same", encoding="utf-8")
        changed = sync_file(
            path=path, content="same", project_root=tmp_path, check=True
        )
        assert changed is False

    def test_check_mode_does_not_create_parent_directories(self, *, tmp_path):
        path = tmp_path / "nested" / "out.txt"
        changed = sync_file(
            path=path, content="hello", project_root=tmp_path, check=True
        )
        assert changed is True
        assert not path.parent.exists()


class TestRemoveFile:
    def test_removes_existing_file(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data", encoding="utf-8")
        changed = remove_file(path=path, project_root=tmp_path)
        assert changed is True
        assert not path.exists()

    def test_noop_when_absent(self, *, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path=path, project_root=tmp_path)
        assert changed is False

    def test_check_mode_does_not_remove(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data", encoding="utf-8")
        changed = remove_file(path=path, project_root=tmp_path, check=True)
        assert changed is True
        assert path.exists()

    def test_check_mode_reports_noop_when_absent(self, *, tmp_path):
        path = tmp_path / "missing.txt"
        changed = remove_file(path=path, project_root=tmp_path, check=True)
        assert changed is False

    def test_removes_each_parent_left_empty_up_to_project_root(self, *, tmp_path):
        path = tmp_path / "a" / "b" / "out.txt"
        path.parent.mkdir(parents=True)
        path.write_text("data", encoding="utf-8")
        remove_file(path=path, project_root=tmp_path)
        assert not (tmp_path / "a").exists()
        assert tmp_path.is_dir()

    def test_keeps_parent_that_holds_other_files(self, *, tmp_path):
        path = tmp_path / "a" / "b" / "out.txt"
        path.parent.mkdir(parents=True)
        path.write_text("data", encoding="utf-8")
        (tmp_path / "a" / "keep.txt").write_text("keep", encoding="utf-8")
        remove_file(path=path, project_root=tmp_path)
        assert not (tmp_path / "a" / "b").exists()
        assert (tmp_path / "a" / "keep.txt").exists()

    def test_keeps_parent_that_is_a_symbolic_link(self, *, tmp_path):
        (tmp_path / "real").mkdir()
        (tmp_path / "link").symlink_to(tmp_path / "real", target_is_directory=True)
        path = tmp_path / "link" / "out.txt"
        path.write_text("data", encoding="utf-8")
        remove_file(path=path, project_root=tmp_path)
        assert not path.exists()
        assert (tmp_path / "link").is_symlink()

    def test_rejects_path_outside_project_root_before_removing(self, *, tmp_path):
        path = tmp_path / "out.txt"
        path.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError, match="is not in the subpath"):
            remove_file(path=path, project_root=tmp_path / "project")
        assert path.exists()

    def test_check_mode_keeps_parent_directories(self, *, tmp_path):
        path = tmp_path / "a" / "out.txt"
        path.parent.mkdir()
        path.write_text("data", encoding="utf-8")
        remove_file(path=path, project_root=tmp_path, check=True)
        assert path.exists()


class TestFileThatCannotBeUsed:
    def test_file_that_cannot_be_read_names_it(self, *, tmp_path):
        (tmp_path / "out.txt").write_bytes(b"\xff")
        with pytest.raises(FileSyncError) as exc_info:
            sync_file(path=Path("out.txt"), content="new", project_root=tmp_path)
        assert str(exc_info.value) == (
            "cannot read out.txt: 'utf-8' codec can't decode byte 0xff in "
            "position 0: invalid start byte"
        )

    def test_file_that_cannot_be_written_names_it(self, *, tmp_path):
        # A file where a parent directory should be fails on every system,
        # with a reason that differs between them.
        (tmp_path / "nested").write_text("", encoding="utf-8")
        path = Path("nested") / "out.txt"
        with pytest.raises(FileSyncError) as exc_info:
            sync_file(path=path, content="new", project_root=tmp_path)
        message = str(exc_info.value)
        assert message.startswith("cannot write nested/out.txt: ")
        assert "Errno" not in message

    def test_file_that_cannot_be_removed_names_it(self, *, tmp_path):
        # Removing a directory as a file fails on every system, with a reason
        # that differs between them.
        (tmp_path / "out.txt").mkdir()
        with pytest.raises(FileSyncError) as exc_info:
            remove_file(path=Path("out.txt"), project_root=tmp_path)
        message = str(exc_info.value)
        assert message.startswith("cannot remove out.txt: ")
        assert "Errno" not in message


class TestSyncFileProjectRootAnchor:
    def test_project_root_anchors_write_independent_of_cwd(
        self, *, tmp_path, monkeypatch
    ):
        # path is project-relative; project_root anchors I/O at tmp_path
        # even when cwd is elsewhere.
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        changed = sync_file(path=rel, content="hello", project_root=tmp_path)

        assert changed is True
        assert (tmp_path / rel).read_text(encoding="utf-8") == "hello"
        # No write under cwd.
        assert not (sub / rel).exists()

    def test_project_root_preserves_relative_path_in_message(
        self, *, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        rel = Path("nested/out.txt")
        sync_file(path=rel, content="hello", project_root=tmp_path)
        out = capsys.readouterr().out
        # Display stays project-relative, with / on every system; absolute
        # path does not leak in.
        assert "Wrote nested/out.txt" in out
        assert str(tmp_path) not in out


class TestRemoveFileProjectRootAnchor:
    def test_project_root_anchors_removal_independent_of_cwd(
        self, *, tmp_path, monkeypatch, capsys
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("nested/out.txt")
        target = tmp_path / rel
        target.parent.mkdir(parents=True)
        target.write_text("data", encoding="utf-8")

        changed = remove_file(path=rel, project_root=tmp_path)
        assert changed is True
        assert not target.exists()
        assert "Removed nested/out.txt" in capsys.readouterr().out
