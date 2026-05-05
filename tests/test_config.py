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
    def test_finds_at_start(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("")
        assert find_pyproject_toml(start=tmp_path) == tmp_path / "pyproject.toml"

    def test_finds_in_parent_of_start(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        assert find_pyproject_toml(start=subdir) == tmp_path / "pyproject.toml"

    def test_returns_none_if_not_found(self, tmp_path):
        assert find_pyproject_toml(start=tmp_path) is None


class TestReadProjectName:
    def test_reads_name_from_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-app"\n')
        assert read_project_name(start=tmp_path) == "my-app"

    def test_falls_back_to_start_name_when_no_pyproject(self, tmp_path):
        assert read_project_name(start=tmp_path) == tmp_path.name

    def test_falls_back_to_start_name_when_no_project_section(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        assert read_project_name(start=tmp_path) == tmp_path.name

    def test_falls_back_to_start_name_when_name_missing(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1"\n')
        assert read_project_name(start=tmp_path) == tmp_path.name


class TestReadSourceRoots:
    def test_reads_source_roots(self, tmp_path):
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text('[tool.uncoded]\nsource-roots = ["src", "tests"]\n')
        roots = read_source_roots(pyproject_path=pyproject_path)
        assert roots == [Path("src"), Path("tests")]

    def test_raises_if_no_uncoded_section(self, tmp_path):
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("[tool.ruff]\n")
        with pytest.raises(LookupError) as excinfo:
            read_source_roots(pyproject_path=pyproject_path)
        # KeyError would be wrong: its __str__ wraps the message in single
        # quotes, which surfaces as "Error: 'No [tool.uncoded] ...'" in
        # the CLI's f-string. LookupError is the parent type that
        # formats cleanly and stays semantically correct.
        assert not isinstance(excinfo.value, KeyError)
        assert "Add [tool.uncoded] source-roots to configure" in str(excinfo.value)


class TestReadInstructionFiles:
    def test_returns_default_when_no_pyproject_toml(self, tmp_path):
        assert read_instruction_files(start=tmp_path) == list(DEFAULT_INSTRUCTION_FILES)

    def test_returns_default_when_key_absent(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\n'
        )
        assert read_instruction_files(start=tmp_path) == list(DEFAULT_INSTRUCTION_FILES)

    def test_reads_configured_list(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[tool.uncoded]\n"
            'source-roots = ["src"]\n'
            'instruction-files = ["CLAUDE.md", "AGENTS.md", "CONVENTIONS.md"]\n'
        )
        assert read_instruction_files(start=tmp_path) == [
            Path("CLAUDE.md"),
            Path("AGENTS.md"),
            Path("CONVENTIONS.md"),
        ]

    def test_empty_list_is_respected(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\ninstruction-files = []\n'
        )
        assert read_instruction_files(start=tmp_path) == []
