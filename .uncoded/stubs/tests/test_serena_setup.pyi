# tests/test_serena_setup.py

import json
from pathlib import Path
import yaml
from uncoded.serena_setup import SERENA_ALLOWED_TOOLS, SERENA_VERSION, setup

REPO_ROOT = Path(__file__).parent.parent
EXPECTED_EXCLUDED_TOOLS = ...
EXPECTED_MCP_ARGS = ...

class TestSetup:

    def _run(self, tmp_path, monkeypatch, name):
        ...

    def test_creates_all_three_files(self, tmp_path, monkeypatch):
        ...

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path, monkeypatch):
        ...

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path, monkeypatch):
        ...

    def test_serena_project_yml_escapes_yaml_special_chars_in_name(self, tmp_path, monkeypatch):
        ...

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path, monkeypatch):
        ...

    def test_idempotent(self, tmp_path, monkeypatch):
        ...

    def test_merges_into_existing_mcp_json(self, tmp_path, monkeypatch):
        ...

    def test_refreshes_stale_serena_entry_in_mcp_json(self, tmp_path, monkeypatch):
        ...

    def test_merges_into_existing_claude_settings(self, tmp_path, monkeypatch):
        ...

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path, monkeypatch):
        ...

    def test_does_not_duplicate_on_second_merge(self, tmp_path, monkeypatch):
        ...

    def test_setup_uses_cwd_name_when_no_pyproject(self, tmp_path, monkeypatch):
        ...

    def test_setup_reads_name_from_pyproject(self, tmp_path, monkeypatch):
        ...

class TestRepoDogfooding:
    """Catch drift between ``uncoded setup``'s templates and this repo's own config."""

    def test_repo_mcp_json_matches_template_contract(self):
        ...

    def test_repo_claude_settings_allowlists_every_serena_tool(self):
        ...

    def test_repo_serena_project_yml_matches_template_contract(self):
        ...
