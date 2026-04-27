# tests/test_skill.py

import os
from pathlib import Path
from uncoded.skill import _SKILL_CONTENT, LEGACY_SKILL_OUTPUTS, SKILL_OUTPUTS, sync_skill

class TestSyncSkill:

    def test_skill_name_and_output_paths(self):
        ...

    def test_writes_skill_files(self, tmp_path):
        ...

    def test_creates_parent_directories(self, tmp_path):
        ...

    def test_returns_true_on_first_write(self, tmp_path):
        ...

    def test_returns_false_when_already_in_sync(self, tmp_path):
        ...

    def test_idempotent(self, tmp_path):
        ...

    def test_check_mode_does_not_write(self, tmp_path):
        ...

    def test_check_mode_reports_change_when_missing(self, tmp_path):
        ...

    def test_check_mode_reports_no_change_when_in_sync(self, tmp_path):
        ...

    def test_removes_legacy_skill_files(self, tmp_path):
        ...

    def test_check_mode_reports_legacy_skill_files_without_removing(self, tmp_path):
        ...
