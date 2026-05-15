# tests/test_cli.py

import sys
import textwrap
from pathlib import Path
import pytest
from uncoded import cli
from uncoded.skill import SKILL_OUTPUTS

def _init_repo(tmp_path, monkeypatch, source_roots):
    ...

class TestSyncApplyMode:
    def test_writes_namespace_map_stubs_and_instruction_file(self, tmp_path, monkeypatch):
        ...

    def test_idempotent_second_run(self, tmp_path, monkeypatch):
        ...

    def test_dedupes_when_claude_md_is_symlink_to_agents_md(self, tmp_path, monkeypatch, capsys):
        ...

    def test_instruction_file_outside_project_uses_absolute_path(self, tmp_path, monkeypatch):
        ...

    def test_error_when_no_pyproject_toml(self, tmp_path, monkeypatch, capsys):
        ...

    def test_error_when_source_root_missing(self, tmp_path, monkeypatch, capsys):
        ...

    def test_error_when_uncoded_section_missing(self, tmp_path, monkeypatch, capsys):
        ...

    def test_skip_warning_emitted_once_per_broken_file(self, tmp_path, monkeypatch, capsys):
        ...

    def test_anchors_reads_and_writes_at_project_root_when_cwd_is_subdir(self, tmp_path, monkeypatch):
        ...

    def test_artefacts_match_when_run_from_subdir_vs_project_root(self, tmp_path, monkeypatch):
        ...

class TestSyncCheckMode:
    def test_returns_one_and_does_not_write_on_empty_repo(self, tmp_path, monkeypatch):
        ...

    def test_returns_zero_when_index_is_up_to_date(self, tmp_path, monkeypatch):
        ...

    def test_returns_one_when_source_changes_after_sync(self, tmp_path, monkeypatch):
        ...

    def test_returns_one_when_source_file_deleted(self, tmp_path, monkeypatch):
        ...

    def test_returns_one_when_instruction_file_drifts(self, tmp_path, monkeypatch):
        ...

    def test_dedupes_when_claude_md_is_symlink_to_agents_md(self, tmp_path, monkeypatch, capsys):
        ...

    def test_error_still_returns_one(self, tmp_path, monkeypatch, capsys):
        ...

class TestMainDispatch:
    def test_sync_subcommand_runs_in_apply_mode(self, tmp_path, monkeypatch):
        ...

    def test_check_subcommand_runs_in_check_mode(self, tmp_path, monkeypatch):
        ...

    def test_check_subcommand_returns_zero_on_fresh_index(self, tmp_path, monkeypatch):
        ...

    def test_setup_subcommand(self, tmp_path, monkeypatch):
        ...

    def test_no_subcommand_is_an_error(self, tmp_path, monkeypatch):
        ...

    def test_unknown_subcommand_is_an_error(self, tmp_path, monkeypatch):
        ...

class TestBodyCommand:
    def test_happy_path_dispatch(self, tmp_path, monkeypatch, capsys):
        ...

    def test_class_method_form(self, tmp_path, monkeypatch, capsys):
        ...

    def test_symbol_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        ...

    def test_file_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        ...

    def test_syntax_error_exits_one(self, tmp_path, monkeypatch, capsys):
        ...

    def test_in_path_resolves_relative_to_cwd(self, tmp_path, monkeypatch, capsys):
        ...

    def test_stdout_is_exact_body(self, tmp_path, monkeypatch, capsys):
        ...

    def test_unsupported_name_path_exits_one(self, tmp_path, monkeypatch, capsys):
        ...

    def test_missing_in_flag_exits_with_two(self, tmp_path, monkeypatch, capsys):
        ...
