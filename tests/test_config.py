import os
from pathlib import Path

import pytest

from uncoded.config import (
    find_pyproject_toml,
    read_instruction_files,
    read_project_name,
    read_source_roots,
)
from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES


class TestFindPyprojectToml:
    def test_finds_in_cwd(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("")
        os.chdir(tmp_path)
        assert find_pyproject_toml() == tmp_path / "pyproject.toml"

    def test_finds_in_parent(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        os.chdir(subdir)
        assert find_pyproject_toml() == tmp_path / "pyproject.toml"

    def test_returns_none_if_not_found(self, tmp_path):
        os.chdir(tmp_path)
        assert find_pyproject_toml() is None


class TestReadProjectName:
    def test_reads_name_from_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-app"\n')
        os.chdir(tmp_path)
        assert read_project_name() == "my-app"

    def test_falls_back_to_cwd_name_when_no_pyproject(self, tmp_path):
        os.chdir(tmp_path)
        assert read_project_name() == tmp_path.name

    def test_falls_back_to_cwd_name_when_no_project_section(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        os.chdir(tmp_path)
        assert read_project_name() == tmp_path.name

    def test_falls_back_to_cwd_name_when_name_missing(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1"\n')
        os.chdir(tmp_path)
        assert read_project_name() == tmp_path.name


class TestReadSourceRoots:
    def test_reads_source_roots(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src", "tests"]\n'
        )
        os.chdir(tmp_path)
        roots = read_source_roots()
        assert roots == [Path("src"), Path("tests")]

    def test_raises_if_no_pyproject_toml(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            read_source_roots()

    def test_raises_if_no_uncoded_section(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        os.chdir(tmp_path)
        with pytest.raises(KeyError):
            read_source_roots()


class TestReadInstructionFiles:
    def test_returns_default_when_no_pyproject_toml(self, tmp_path):
        os.chdir(tmp_path)
        assert read_instruction_files() == list(DEFAULT_INSTRUCTION_FILES)

    def test_returns_default_when_key_absent(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\n'
        )
        os.chdir(tmp_path)
        assert read_instruction_files() == list(DEFAULT_INSTRUCTION_FILES)

    def test_reads_configured_list(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[tool.uncoded]\n"
            'source-roots = ["src"]\n'
            'instruction-files = ["CLAUDE.md", "AGENTS.md", "CONVENTIONS.md"]\n'
        )
        os.chdir(tmp_path)
        assert read_instruction_files() == [
            Path("CLAUDE.md"),
            Path("AGENTS.md"),
            Path("CONVENTIONS.md"),
        ]

    def test_empty_list_is_respected(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\ninstruction-files = []\n'
        )
        os.chdir(tmp_path)
        assert read_instruction_files() == []
