# tests/test_serena_setup.py

import json
import os
from pathlib import Path
import yaml
from uncoded.serena_setup import SERENA_ALLOWED_TOOLS, SERENA_VERSION, read_project_name, setup_serena

REPO_ROOT = Path(__file__).parent.parent  # L14
EXPECTED_EXCLUDED_TOOLS = ...  # L20-31

class TestReadProjectName:  # L34-52

    def test_reads_name_from_pyproject_toml(self, tmp_path):  # L35-38
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L40-42
        ...

    def test_falls_back_to_cwd_name_when_no_project_section(self, tmp_path):  # L44-47
        ...

    def test_falls_back_to_cwd_name_when_name_missing(self, tmp_path):  # L49-52
        ...

class TestSetupSerena:  # L55-169

    def _run(self, tmp_path, name):  # L56-59
        ...

    def test_creates_all_three_files(self, tmp_path):  # L61-65
        ...

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path):  # L67-75
        ...

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path):  # L77-84
        ...

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path):  # L86-91
        ...

    def test_idempotent(self, tmp_path):  # L93-101
        ...

    def test_merges_into_existing_mcp_json(self, tmp_path):  # L103-111
        ...

    def test_refreshes_stale_serena_entry_in_mcp_json(self, tmp_path):  # L113-127
        ...

    def test_merges_into_existing_claude_settings(self, tmp_path):  # L129-145
        ...

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path):  # L147-153
        ...

    def test_does_not_duplicate_on_second_merge(self, tmp_path):  # L155-163
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L165-169
        ...

class TestRepoDogfooding:  # L172-199
    """Catch drift between setup-serena's templates and this repo's own config."""

    def test_repo_mcp_json_pins_same_serena_version(self):  # L182-185
        ...

    def test_repo_claude_settings_allowlists_every_serena_tool(self):  # L187-193
        ...

    def test_repo_serena_project_yml_matches_template_contract(self):  # L195-199
        ...
