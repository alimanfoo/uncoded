import os
from pathlib import Path

from uncoded.skill import (
    _SKILL_CONTENT,
    LEGACY_SKILL_OUTPUTS,
    SKILL_OUTPUTS,
    sync_skill,
)


class TestSyncSkill:
    def test_skill_name_and_output_paths(self):
        assert [
            Path(".claude/skills/coherence-review/SKILL.md"),
            Path(".agents/skills/coherence-review/SKILL.md"),
        ] == SKILL_OUTPUTS
        assert "name: coherence-review\n" in _SKILL_CONTENT
        assert "name: uncoded-review\n" not in _SKILL_CONTENT

    def test_writes_skill_files(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        for path in SKILL_OUTPUTS:
            skill_path = tmp_path / path
            assert skill_path.exists()
            assert skill_path.read_text() == _SKILL_CONTENT

    def test_creates_parent_directories(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        for path in SKILL_OUTPUTS:
            assert (tmp_path / path).parent.is_dir()

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
        mtimes = [(tmp_path / path).stat().st_mtime_ns for path in SKILL_OUTPUTS]
        sync_skill(check=False)
        assert [
            (tmp_path / path).stat().st_mtime_ns for path in SKILL_OUTPUTS
        ] == mtimes

    def test_check_mode_does_not_write(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=True)
        for path in SKILL_OUTPUTS:
            assert not (tmp_path / path).exists()

    def test_check_mode_reports_change_when_missing(self, tmp_path):
        os.chdir(tmp_path)
        assert sync_skill(check=True) is True

    def test_check_mode_reports_no_change_when_in_sync(self, tmp_path):
        os.chdir(tmp_path)
        sync_skill(check=False)
        assert sync_skill(check=True) is False

    def test_removes_legacy_skill_files(self, tmp_path):
        os.chdir(tmp_path)
        for path in LEGACY_SKILL_OUTPUTS:
            legacy_path = tmp_path / path
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text("old skill\n")

        assert sync_skill(check=False) is True

        for path in LEGACY_SKILL_OUTPUTS:
            assert not (tmp_path / path).exists()

    def test_check_mode_reports_legacy_skill_files_without_removing(self, tmp_path):
        os.chdir(tmp_path)
        for path in LEGACY_SKILL_OUTPUTS:
            legacy_path = tmp_path / path
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text("old skill\n")

        assert sync_skill(check=True) is True

        for path in LEGACY_SKILL_OUTPUTS:
            assert (tmp_path / path).exists()
