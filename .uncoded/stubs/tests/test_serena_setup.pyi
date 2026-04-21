# tests/test_serena_setup.py

import json
import os
import yaml
from uncoded.serena_setup import SERENA_ALLOWED_TOOLS, SERENA_VERSION, read_project_name, setup_serena

class TestReadProjectName:  # L14-32

    def test_reads_name_from_pyproject_toml(self, tmp_path):  # L15-18
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L20-22
        ...

    def test_falls_back_to_cwd_name_when_no_project_section(self, tmp_path):  # L24-27
        ...

    def test_falls_back_to_cwd_name_when_name_missing(self, tmp_path):  # L29-32
        ...

class TestSetupSerena:  # L35-131

    def _run(self, tmp_path, name):  # L36-39
        ...

    def test_creates_all_three_files(self, tmp_path):  # L41-45
        ...

    def test_mcp_json_is_valid_and_pins_version(self, tmp_path):  # L47-55
        ...

    def test_serena_project_yml_uses_ty_and_ignores_uncoded(self, tmp_path):  # L57-63
        ...

    def test_claude_settings_enables_serena_and_allowlists_tools(self, tmp_path):  # L65-69
        ...

    def test_idempotent(self, tmp_path):  # L71-79
        ...

    def test_merges_into_existing_mcp_json(self, tmp_path):  # L81-89
        ...

    def test_merges_into_existing_claude_settings(self, tmp_path):  # L91-107
        ...

    def test_does_not_overwrite_existing_serena_project_yml(self, tmp_path):  # L109-115
        ...

    def test_does_not_duplicate_on_second_merge(self, tmp_path):  # L117-125
        ...

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):  # L127-131
        ...
