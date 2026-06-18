# tests/test_config.py

from pathlib import Path
from uncoded.config import Config, find_pyproject_toml, read_config
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

class TestFindPyprojectToml:
    def test_finds_at_start(self, tmp_path):
        ...

    def test_finds_in_parent_of_start(self, tmp_path):
        ...

    def test_returns_none_if_not_found(self, tmp_path):
        ...

class TestReadConfig:
    def test_returns_none_when_no_pyproject(self, tmp_path):
        ...

    def test_source_roots_read(self, tmp_path):
        ...

    def test_doc_roots_read(self, tmp_path):
        ...

    def test_both_roots_empty_when_section_absent(self, tmp_path):
        ...

    def test_project_root_is_pyproject_parent(self, tmp_path):
        ...

    def test_finds_in_parent_directory(self, tmp_path):
        ...

    def test_instruction_files_default_when_key_absent(self, tmp_path):
        ...

    def test_instruction_files_configured(self, tmp_path):
        ...

    def test_instruction_files_empty_list_respected(self, tmp_path):
        ...

    def test_returns_frozen_dataclass(self, tmp_path):
        ...
