# tests/test_cli.py

import os
import sys
import textwrap
import pytest
from uncoded import cli

def _init_repo(tmp_path, source_roots):  # L17-33
    """Set up a minimal repo: pyproject.toml + source root + chdir."""
    ...

class TestBuildApplyMode:  # L36-83

    def test_writes_namespace_map_stubs_and_instruction_file(self, tmp_path):  # L37-44
        ...

    def test_idempotent_second_run(self, tmp_path):  # L46-62
        ...

    def test_error_when_no_pyproject_toml(self, tmp_path, capsys):  # L64-67
        ...

    def test_error_when_source_root_missing(self, tmp_path, capsys):  # L69-83
        ...

class TestBuildCheckMode:  # L86-143

    def test_returns_one_and_does_not_write_on_empty_repo(self, tmp_path):  # L87-94
        ...

    def test_returns_zero_when_index_is_up_to_date(self, tmp_path):  # L96-100
        ...

    def test_returns_one_when_source_changes_after_build(self, tmp_path):  # L102-113
        ...

    def test_returns_one_when_source_file_deleted(self, tmp_path):  # L115-124
        ...

    def test_returns_one_when_instruction_file_drifts(self, tmp_path):  # L126-137
        ...

    def test_error_still_returns_one(self, tmp_path, capsys):  # L139-143
        ...

class TestMainFlagRouting:  # L146-187

    def test_no_args_runs_build_in_apply_mode(self, tmp_path, monkeypatch):  # L147-153
        ...

    def test_check_flag_runs_build_in_check_mode(self, tmp_path, monkeypatch):  # L155-162
        ...

    def test_check_flag_returns_zero_on_fresh_index(self, tmp_path, monkeypatch):  # L164-170
        ...

    def test_check_is_ignored_by_setup_serena(self, tmp_path, monkeypatch):  # L172-178
        ...

    def test_check_flag_rejected_with_setup_serena(self, tmp_path, monkeypatch):  # L180-187
        ...
