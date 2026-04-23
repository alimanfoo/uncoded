# tests/test_serena_setup.py

import json
import os
from pathlib import Path
import yaml
from uncoded.serena_setup import SERENA_ALLOWED_TOOLS, SERENA_VERSION, read_project_name, setup_serena

REPO_ROOT = Path(__file__).parent.parent  # L14
EXPECTED_EXCLUDED_TOOLS = ...  # L20-32

class TestReadProjectName:  # L35-53

    def test_reads_name_from_pyproject_toml(self, tmp_path):  # L36-39
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L41-43
        ...

    def test_falls_back_to_cwd_name_when_no_project_section(self, tmp_path):  # L45-48
        ...

    def test_falls_back_to_cwd_name_when_name_missing(self, tmp_path):  # L50-53
        ...

class TestSetupSerena:  # L56-168

    def _run(self, tmp_path, name):  # L57-60
        ...

    def test_creates_all_three_files(self, tmp_path):  # L62-66
        ...

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path):  # L68-76
        ...

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path):  # L78-84
        ...

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path):  # L86-90
        ...

    def test_idempotent(self, tmp_path):  # L92-100
        ...

    def test_merges_into_existing_mcp_json(self, tmp_path):  # L102-110
        ...

    def test_refreshes_stale_serena_entry_in_mcp_json(self, tmp_path):  # L112-126
        ...

    def test_merges_into_existing_claude_settings(self, tmp_path):  # L128-144
        ...

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path):  # L146-152
        ...

    def test_does_not_duplicate_on_second_merge(self, tmp_path):  # L154-162
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L164-168
        ...

class TestRepoDogfooding:  # L171-198
    """Catch drift between setup-serena's templates and this repo's own config."""

    def test_repo_mcp_json_pins_same_serena_version(self):  # L181-184
        ...

    def test_repo_claude_settings_allowlists_every_serena_tool(self):  # L186-192
        ...

    def test_repo_serena_project_yml_matches_template_contract(self):  # L194-198
        ...
