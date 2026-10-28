from pathlib import Path

import pytest

from uncoded import __version__
from uncoded.config import (
    Config,
    ConfigError,
    find_config,
    read_config,
)


class TestFindConfig:
    def test_returns_none_when_no_config_file(self, *, tmp_path):
        assert find_config(start=tmp_path) is None


class TestReadConfig:
    # --- pyproject.toml ---

    def test_raises_when_no_config_file(self, *, tmp_path):
        with pytest.raises(ConfigError, match=r"No configuration file found"):
            read_config(start=tmp_path)

    def test_raises_when_pyproject_has_no_uncoded_table(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        with pytest.raises(ConfigError, match=r"No configuration file found"):
            read_config(start=tmp_path)

    def test_source_roots_read_from_pyproject(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["src", "tests"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config.source_roots == [Path("src"), Path("tests")]

    def test_doc_roots_read_from_pyproject(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\ndoc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config.doc_roots == [Path("docs")]

    def test_both_roots_empty_when_uncoded_table_is_empty(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.uncoded]\n", encoding="utf-8")
        config = read_config(start=tmp_path)
        assert config.source_roots == []
        assert config.doc_roots == []

    def test_passes_over_subproject_pyproject_without_uncoded_table(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nsource-roots = ["pkg"]\n', encoding="utf-8"
        )
        subproject = tmp_path / "pkg"
        subproject.mkdir()
        (subproject / "pyproject.toml").write_text(
            '[project]\nname = "pkg"\n', encoding="utf-8"
        )
        config = read_config(start=subproject)
        assert config.project_root == tmp_path
        assert config.source_roots == [Path("pkg")]

    def test_project_root_is_config_file_parent(self, *, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        config = read_config(start=tmp_path)
        assert config.project_root == tmp_path

    def test_finds_pyproject_in_parent_directory(self, *, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        config = read_config(start=subdir)
        assert config.project_root == tmp_path

    def test_returns_frozen_dataclass(self, *, tmp_path):
        toml = '[tool.uncoded]\nsource-roots = ["src"]\n'
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        config = read_config(start=tmp_path)
        assert isinstance(config, Config)

    def test_required_version_read_from_pyproject(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.uncoded]\nrequired-version = "3.1.0"\n', encoding="utf-8"
        )
        assert read_config(start=tmp_path).required_version == "3.1.0"

    def test_required_version_is_none_when_unset(self, *, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.uncoded]\n", encoding="utf-8")
        assert read_config(start=tmp_path).required_version is None

    # --- .uncoded.toml ---

    def test_finds_uncoded_toml_when_no_pyproject(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config.project_root == tmp_path
        assert config.doc_roots == [Path("docs")]
        assert config.source_roots == []

    def test_uncoded_toml_top_level_keys(self, *, tmp_path):
        # source-roots and doc-roots at the top level with no [tool.uncoded] wrapper.
        (tmp_path / ".uncoded.toml").write_text(
            'source-roots = ["src"]\ndoc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config.source_roots == [Path("src")]
        assert config.doc_roots == [Path("docs")]

    def test_required_version_read_from_uncoded_toml(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_text(
            'required-version = "3.1.0"\n', encoding="utf-8"
        )
        assert read_config(start=tmp_path).required_version == "3.1.0"

    def test_error_when_both_configure_uncoded_in_same_directory(self, *, tmp_path):
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

    def test_finds_uncoded_toml_beside_pyproject_without_uncoded_table(
        self, *, tmp_path
    ):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        (tmp_path / ".uncoded.toml").write_text(
            'doc-roots = ["docs"]\n', encoding="utf-8"
        )
        config = read_config(start=tmp_path)
        assert config.project_root == tmp_path
        assert config.doc_roots == [Path("docs")]

    def test_uncoded_toml_wins_when_nearer_than_pyproject(self, *, tmp_path):
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
        assert config.project_root == child
        assert config.doc_roots == [Path("from-child")]

    def test_pyproject_wins_when_nearer_than_uncoded_toml(self, *, tmp_path):
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
        assert config.project_root == child
        assert config.source_roots == [Path("from-child")]

    def test_uncoded_pyproject_and_uncoded_toml_in_different_dirs_no_error(
        self, *, tmp_path
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
        assert config.doc_roots == [Path("from-child")]

    def test_skips_uncoded_directory_as_config_home(self, *, tmp_path):
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
        assert config.project_root == tmp_path
        assert config.source_roots == [Path("src")]


class TestConfigFileThatCannotBeUsed:
    def test_not_valid_toml(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_text("source-roots\n", encoding="utf-8")
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert str(exc_info.value) == (
            f"{(tmp_path / '.uncoded.toml').resolve().as_posix()}: not valid TOML: "
            "Expected '=' after a key in a key/value pair (at line 1, column 13)"
        )

    def test_not_valid_toml_without_uncoded_settings_on_the_way_up(self, *, tmp_path):
        # The search cannot tell whether the file configures uncoded, so it
        # stops there rather than pass over it.
        (tmp_path / ".uncoded.toml").write_text(
            'source-roots = ["pkg"]\n', encoding="utf-8"
        )
        subproject = tmp_path / "pkg"
        subproject.mkdir()
        (subproject / "pyproject.toml").write_text("[project\n", encoding="utf-8")
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=subproject)
        assert str(exc_info.value).startswith(
            f"{(subproject / 'pyproject.toml').resolve().as_posix()}: not valid TOML: "
        )

    def test_not_utf8(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_bytes(b"\xff\n")
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert str(exc_info.value) == (
            f"{(tmp_path / '.uncoded.toml').resolve().as_posix()}: not valid TOML: "
            "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
        )

    def test_cannot_be_read(self, *, tmp_path):
        # Opening a directory fails on every system, with a reason that
        # differs between them.
        (tmp_path / "pyproject.toml").mkdir()
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        message = str(exc_info.value)
        assert message.startswith(
            f"{(tmp_path / 'pyproject.toml').resolve().as_posix()}: "
        )
        assert "\n" not in message
        assert "Errno" not in message

    @pytest.mark.parametrize(
        ("toml", "problem"),
        [
            ('tool = "x"\n', "tool is not a table"),
            ("[tool]\nuncoded = 5\n", "tool.uncoded is not a table"),
            (
                '[tool.uncoded]\nsource-roots = "src"\n',
                "source-roots is not a list of strings",
            ),
            (
                "[tool.uncoded]\ndoc-roots = [1]\n",
                "doc-roots is not a list of strings",
            ),
            (
                "[tool.uncoded]\nrequired-version = 3.1\n",
                'required-version is not one exact version, such as "3.1.0"',
            ),
        ],
    )
    def test_setting_of_the_wrong_type_in_pyproject(self, *, tmp_path, toml, problem):
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert str(exc_info.value) == (
            f"{(tmp_path / 'pyproject.toml').resolve().as_posix()}: {problem}"
        )

    def test_setting_of_the_wrong_type_in_uncoded_toml(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_text(
            'source-roots = ["src", ["tests"]]\n', encoding="utf-8"
        )
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert str(exc_info.value) == (
            f"{(tmp_path / '.uncoded.toml').resolve().as_posix()}: "
            "source-roots is not a list of strings"
        )

    @pytest.mark.parametrize(
        "version", ["3.1", "3", "~=3.1.0", "==3.1.0", "3.1.0, <4", "v3.1.0", ""]
    )
    def test_required_version_that_is_not_one_exact_version(self, *, tmp_path, version):
        (tmp_path / ".uncoded.toml").write_text(
            f'required-version = "{version}"\n', encoding="utf-8"
        )
        with pytest.raises(ConfigError) as exc_info:
            read_config(start=tmp_path)
        assert str(exc_info.value) == (
            f"{(tmp_path / '.uncoded.toml').resolve().as_posix()}: "
            'required-version is not one exact version, such as "3.1.0"'
        )

    def test_required_version_that_is_a_list(self, *, tmp_path):
        (tmp_path / ".uncoded.toml").write_text(
            'required-version = ["3.1.0"]\n', encoding="utf-8"
        )
        with pytest.raises(ConfigError, match="required-version is not one exact"):
            read_config(start=tmp_path)

    @pytest.mark.parametrize(
        "version",
        [
            "3.1.0",
            "10.20.30",
            "3.1.0rc1",
            "3.1.0.post1",
            "3.1.0.dev5+g1a2b3c4",
            "3.1.0.dev5+g1a2b3c4.d20261028",
            __version__,
        ],
    )
    def test_required_version_that_is_one_exact_version(self, *, tmp_path, version):
        (tmp_path / ".uncoded.toml").write_text(
            f'required-version = "{version}"\n', encoding="utf-8"
        )
        assert read_config(start=tmp_path).required_version == version
