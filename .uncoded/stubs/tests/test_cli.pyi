# tests/test_cli.py

import os
import sys
import textwrap
import pytest
from uncoded import cli
from uncoded.skill import SKILL_OUTPUTS

def _init_repo(tmp_path, source_roots):
    """Set up a minimal repo: pyproject.toml + source root + chdir."""
    ...

class TestSyncApplyMode:

    def test_writes_namespace_map_stubs_and_instruction_file(self, tmp_path):
        ...

    def test_idempotent_second_run(self, tmp_path):
        ...

    def test_error_when_no_pyproject_toml(self, tmp_path, capsys):
        ...

    def test_error_when_source_root_missing(self, tmp_path, capsys):
        ...

class TestSyncCheckMode:

    def test_returns_one_and_does_not_write_on_empty_repo(self, tmp_path):
        ...

    def test_returns_zero_when_index_is_up_to_date(self, tmp_path):
        ...

    def test_returns_one_when_source_changes_after_sync(self, tmp_path):
        ...

    def test_returns_one_when_source_file_deleted(self, tmp_path):
        ...

    def test_returns_one_when_instruction_file_drifts(self, tmp_path):
        ...

    def test_error_still_returns_one(self, tmp_path, capsys):
        ...

class TestMainDispatch:

    def test_sync_subcommand_runs_in_apply_mode(self, tmp_path, monkeypatch):
        ...

    def test_check_subcommand_runs_in_check_mode(self, tmp_path, monkeypatch):
        ...

    def test_check_subcommand_returns_zero_on_fresh_index(self, tmp_path, monkeypatch):
        ...

    def test_setup_serena_subcommand(self, tmp_path, monkeypatch):
        ...

    def test_no_subcommand_is_an_error(self, tmp_path, monkeypatch):
        ...

    def test_unknown_subcommand_is_an_error(self, tmp_path, monkeypatch):
        ...
