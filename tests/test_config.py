from pathlib import Path

import pytest

from uncoded.config import Config, ConfigError, find_pyproject_toml, read_config


class TestFindPyprojectToml:
    def test_finds_at_start(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        assert find_pyproject_toml(start=tmp_path) == tmp_path / "pyproject.toml"

    def test_finds_in_parent_of_start(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        assert find_pyproject_toml(start=subdir) == tmp_path / "pyproject.toml"

    def test_returns_none_if_not_found(self, tmp_path):
        assert find_pyproject_toml(start=tmp_path) is None


class TestReadConfig:
    # --- pyproject.toml ---

    def test_returns_none_when_no_config_file(self, tmp_path):
        assert read_config(start=tmp_path) is None

    def test_source_roots_read_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src", "tests"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.source_roots == [Path("src"), Path("tests")]

    def test_doc_roots_read_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\ndoc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.doc_roots == [Path("docs")]

    def test_both_roots_empty_when_section_absent(self, tmp_path):
        # Bare pyproject (no [tool.uncoded]) with no sibling .uncoded.toml is
        # still a config home; roots default to empty → "nothing to index".
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.source_roots == []
        assert config.doc_roots == []

    def test_project_root_is_config_file_parent(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.project_root == tmp_path

    def test_finds_pyproject_in_parent_directory(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        config = read_config(start=subdir)
        assert config is not None
        assert config.project_root == tmp_path

    def test_returns_frozen_dataclass(self, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        config = read_config(start=tmp_path)
        assert isinstance(config, Config)

    # --- .uncoded.toml ---

    def test_finds_uncoded_toml_when_no_pyproject(self, tmp_path):
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.project_root == tmp_path
        assert config.doc_roots == [Path("docs")]
        assert config.source_roots == []

    def test_uncoded_toml_top_level_keys(self, tmp_path):
        # source-roots and doc-roots at the top level with no [tool.uncoded] wrapper.
        (tmp_path / ".uncoded.toml").write_text(
            'source-roots = ["src"]\ndoc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.source_roots == [Path("src")]
        assert config.doc_roots == [Path("docs")]

    def test_error_when_both_configure_uncoded_in_same_directory(self, tmp_path):
        # pyproject.toml with [tool.uncoded] AND .uncoded.toml → ConfigError.
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\n', encoding="utf-8"
        )
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert "pyproject.toml" in str(exc_info.value)
        assert ".uncoded.toml" in str(exc_info.value)

    def test_uncoded_toml_wins_over_bare_pyproject(self, tmp_path):
        # Bare pyproject (no [tool.uncoded]) + sibling .uncoded.toml →
        # the .uncoded.toml is used, not the bare pyproject.
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config is not None
        assert config.project_root == tmp_path
        assert config.doc_roots == [Path("docs")]

    def test_uncoded_toml_wins_when_nearer_than_pyproject(self, tmp_path):
        # .uncoded.toml in child, pyproject.toml in parent → child wins.
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["from-parent"]\n', encoding="utf-8"
        )
        child = tmp_path / "child"
        child.mkdir()
        (child / ".uncoded.toml").write_text(
            'doc-roots = ["from-child"]\n', encoding="utf-8"
        )
        config = read_config(start=child)
        assert config is not None
        assert config.project_root == child
        assert config.doc_roots == [Path("from-child")]

    def test_pyproject_wins_when_nearer_than_uncoded_toml(self, tmp_path):
        # pyproject.toml in child, .uncoded.toml in parent → child wins.
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["from-parent"]\n', encoding="utf-8"
        )
        child = tmp_path / "child"
        child.mkdir()
        (child / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["from-child"]\n', encoding="utf-8"
        )
        config = read_config(start=child)
        assert config is not None
        assert config.project_root == child
        assert config.source_roots == [Path("from-child")]

    def test_uncoded_pyproject_and_uncoded_toml_in_different_dirs_no_error(
        self, tmp_path
    ):
        # [tool.uncoded] pyproject in parent, .uncoded.toml in child:
        # the nearer .uncoded.toml wins — no error.
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["from-parent"]\n', encoding="utf-8"
        )
        child = tmp_path / "child"
        child.mkdir()
        (child / ".uncoded.toml").write_text(
            'doc-roots = ["from-child"]\n', encoding="utf-8"
        )
        config = read_config(start=child)
        assert config is not None
        assert config.doc_roots == [Path("from-child")]

    def test_skips_uncoded_directory_as_config_home(self, tmp_path):
        # A .uncoded.toml sitting inside a .uncoded/ directory is not a
        # config home — the walk skips any directory named .uncoded.
        uncoded_dir = tmp_path / ".uncoded"
        uncoded_dir.mkdir()
        (uncoded_dir / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        # The real config is one level up.
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src"]\n', encoding="utf-8"
        )
        config = read_config(start=uncoded_dir)
        assert config is not None
        assert config.project_root == tmp_path
        assert config.source_roots == [Path("src")]
