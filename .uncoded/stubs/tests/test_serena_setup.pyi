# tests/test_serena_setup.py

import json
import os
from pathlib import Path
import yaml
from uncoded.serena_setup import SERENA_ALLOWED_TOOLS, SERENA_VERSION, read_project_name, setup_serena

REPO_ROOT = Path(__file__).parent.parent  # L14

class TestReadProjectName:  # L17-35

    def test_reads_name_from_pyproject_toml(self, tmp_path):  # L18-21
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L23-25
        ...

    def test_falls_back_to_cwd_name_when_no_project_section(self, tmp_path):  # L27-30
        ...

    def test_falls_back_to_cwd_name_when_name_missing(self, tmp_path):  # L32-35
        ...

class TestSetupSerena:  # L38-150

    def _run(self, tmp_path, name):  # L39-42
        ...

    def test_creates_all_three_files(self, tmp_path):  # L44-48
        ...

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path):  # L50-58
        ...

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path):  # L60-66
        ...

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path):  # L68-72
        ...

    def test_idempotent(self, tmp_path):  # L74-82
        ...

    def test_merges_into_existing_mcp_json(self, tmp_path):  # L84-92
        ...

    def test_refreshes_stale_serena_entry_in_mcp_json(self, tmp_path):  # L94-108
        ...

    def test_merges_into_existing_claude_settings(self, tmp_path):  # L110-126
        ...

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path):  # L128-134
        ...

    def test_does_not_duplicate_on_second_merge(self, tmp_path):  # L136-144
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L146-150
        ...

class TestRepoDogfooding:  # L153-180
    """Catch drift between setup-serena's templates and this repo's own config."""

    def test_repo_mcp_json_pins_same_serena_version(self):  # L163-166
        ...

    def test_repo_claude_settings_allowlists_every_serena_tool(self):  # L168-174
        ...

    def test_repo_serena_project_yml_matches_template_contract(self):  # L176-180
        ...
