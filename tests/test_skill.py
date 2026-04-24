import os

from uncoded.skill import _SKILL_CONTENT, SKILL_OUTPUT, sync_skill


class TestSyncSkill:
    def test_writes_skill_file(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        skill_path = tmp_path / SKILL_OUTPUT
        assert skill_path.exists()
        assert skill_path.read_text() == _SKILL_CONTENT

    def test_creates_parent_directories(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        assert (tmp_path / ".claude" / "skills" / "uncoded-review").is_dir()

    def test_returns_true_on_first_write(self, tmp_path):
        os.chdir(tmp_path)
        assert sync_skill(check=False) is True

    def test_returns_false_when_already_in_sync(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        assert sync_skill(check=False) is False

    def test_idempotent(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        mtime = (tmp_path / SKILL_OUTPUT).stat().st_mtime_ns
        sync_skill(check=False)
        assert (tmp_path / SKILL_OUTPUT).stat().st_mtime_ns == mtime

    def test_check_mode_does_not_write(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=True)
        assert not (tmp_path / SKILL_OUTPUT).exists()

    def test_check_mode_reports_change_when_missing(self, tmp_path):
        os.chdir(tmp_path)
        assert sync_skill(check=True) is True

    def test_check_mode_reports_no_change_when_in_sync(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        assert sync_skill(check=True) is False
