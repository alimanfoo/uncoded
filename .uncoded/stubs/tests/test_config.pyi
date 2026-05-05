# tests/test_config.py

from pathlib import Path
import pytest
from uncoded.config import find_pyproject_toml, read_instruction_files, read_project_name, read_source_roots
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES

class TestFindPyprojectToml:

    def test_finds_at_start(self, tmp_path):
        ...

    def test_finds_in_parent_of_start(self, tmp_path):
        ...

    def test_returns_none_if_not_found(self, tmp_path):
        ...

class TestReadProjectName:

    def test_reads_name_from_pyproject_toml(self, tmp_path):
        ...

    def test_falls_back_to_start_name_when_no_pyproject(self, tmp_path):
        ...

    def test_falls_back_to_start_name_when_no_project_section(self, tmp_path):
        ...

    def test_falls_back_to_start_name_when_name_missing(self, tmp_path):
        ...

class TestReadSourceRoots:

    def test_reads_source_roots(self, tmp_path):
        ...

    def test_raises_if_no_uncoded_section(self, tmp_path):
        ...

class TestReadInstructionFiles:

    def test_returns_default_when_no_pyproject_toml(self, tmp_path):
        ...

    def test_returns_default_when_key_absent(self, tmp_path):
        ...

    def test_reads_configured_list(self, tmp_path):
        ...

    def test_empty_list_is_respected(self, tmp_path):
        ...
