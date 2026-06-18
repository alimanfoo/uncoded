# tests/test_config.py

from pathlib import Path
import pytest
from uncoded.config import Config, ConfigError, find_pyproject_toml, read_config
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

class TestFindPyprojectToml:
    def test_finds_at_start(self, tmp_path):
        ...

    def test_finds_in_parent_of_start(self, tmp_path):
        ...

    def test_returns_none_if_not_found(self, tmp_path):
        ...

class TestReadConfig:
    def test_returns_none_when_no_config_file(self, tmp_path):
        ...

    def test_source_roots_read_from_pyproject(self, tmp_path):
        ...

    def test_doc_roots_read_from_pyproject(self, tmp_path):
        ...

    def test_both_roots_empty_when_section_absent(self, tmp_path):
        ...

    def test_project_root_is_config_file_parent(self, tmp_path):
        ...

    def test_finds_pyproject_in_parent_directory(self, tmp_path):
        ...

    def test_instruction_files_default_when_key_absent(self, tmp_path):
        ...

    def test_instruction_files_configured(self, tmp_path):
        ...

    def test_instruction_files_empty_list_respected(self, tmp_path):
        ...

    def test_returns_frozen_dataclass(self, tmp_path):
        ...

    def test_finds_uncoded_toml_when_no_pyproject(self, tmp_path):
        ...

    def test_uncoded_toml_top_level_keys(self, tmp_path):
        ...

    def test_error_when_both_configure_uncoded_in_same_directory(self, tmp_path):
        ...

    def test_uncoded_toml_wins_over_bare_pyproject(self, tmp_path):
        ...

    def test_uncoded_toml_wins_when_nearer_than_pyproject(self, tmp_path):
        ...

    def test_pyproject_wins_when_nearer_than_uncoded_toml(self, tmp_path):
        ...

    def test_uncoded_pyproject_and_uncoded_toml_in_different_dirs_no_error(self, tmp_path):
        ...

    def test_skips_uncoded_directory_as_config_home(self, tmp_path):
        ...
