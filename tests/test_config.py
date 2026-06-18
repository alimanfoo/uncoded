from pathlib import Path

from uncoded.config import Config, find_pyproject_toml, read_config
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


class TestReadConfig:
    def test_returns_none_when_no_pyproject(self, tmp_path):
        assert read_config(start=tmp_path) is None

    def test_source_roots_read(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src", "tests"]\n'
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.source_roots == [Path("src"), Path("tests")]

    def test_doc_roots_read(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\ndoc-roots = ["docs"]\n'
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.doc_roots == [Path("docs")]

    def test_both_roots_empty_when_section_absent(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.source_roots == []
        assert config.doc_roots == []

    def test_project_root_is_pyproject_parent(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml)
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.project_root == tmp_path

    def test_finds_in_parent_directory(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml)
        subdir = tmp_path / "sub"
        subdir.mkdir()
        config = read_config(start=subdir)
        assert config is not None
        assert config.project_root == tmp_path

    def test_instruction_files_default_when_key_absent(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml)
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.instruction_files == list(DEFAULT_INSTRUCTION_FILES)

    def test_instruction_files_configured(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[tool.uncoded]\n"
            'source-roots = ["src"]\n'
            'instruction-files = ["CLAUDE.md", "AGENTS.md", "CONVENTIONS.md"]\n'
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.instruction_files == [
            Path("CLAUDE.md"),
            Path("AGENTS.md"),
            Path("CONVENTIONS.md"),
        ]

    def test_instruction_files_empty_list_respected(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\ninstruction-files = []\n'
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.instruction_files == []

    def test_returns_frozen_dataclass(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml)
        config = read_config(start=tmp_path)
        assert isinstance(config, Config)
