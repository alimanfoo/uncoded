"""End-to-end tests for the uncoded CLI.

These exercise :func:`cli._sync` (and :func:`cli.main` for subcommand
dispatch) on a real filesystem. The sister modules have their own unit
tests; this suite covers the orchestration and the ``check`` exit-code
contract.
"""

import os
import sys
import textwrap

import pytest

from uncoded import cli
from uncoded.skill import SKILL_OUTPUTS


def _init_repo(tmp_path, source_roots=("src",)):
    """Set up a minimal repo: pyproject.toml + source root + chdir."""
    roots_list = ", ".join(f'"{r}"' for r in source_roots)
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""\
            [project]
            name = "demo"

            [tool.uncoded]
            source-roots = [{roots_list}]
            """
        )
    )
    for root in source_roots:
        (tmp_path / root).mkdir()
    os.chdir(tmp_path)


class TestSyncApplyMode:
    def test_writes_namespace_map_stubs_and_instruction_file(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")

        assert cli._sync() == 0
        assert (tmp_path / ".uncoded" / "namespace.yaml").exists()
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        for skill_path in SKILL_OUTPUTS:
            assert (tmp_path / skill_path).exists()

    def test_idempotent_second_run(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()
        ns_mtime = (tmp_path / ".uncoded" / "namespace.yaml").stat().st_mtime_ns
        stub_mtime = (
            (tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi").stat().st_mtime_ns
        )
        claude_mtime = (tmp_path / "CLAUDE.md").stat().st_mtime_ns
        skill_mtimes = [(tmp_path / p).stat().st_mtime_ns for p in SKILL_OUTPUTS]

        # A second run with no source changes must not rewrite any artifact.
        assert cli._sync() == 0
        assert (tmp_path / ".uncoded" / "namespace.yaml").stat().st_mtime_ns == ns_mtime
        assert (
            tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi"
        ).stat().st_mtime_ns == stub_mtime
        assert (tmp_path / "CLAUDE.md").stat().st_mtime_ns == claude_mtime
        assert [
            (tmp_path / p).stat().st_mtime_ns for p in SKILL_OUTPUTS
        ] == skill_mtimes

    def test_error_when_no_pyproject_toml(self, tmp_path, capsys):
        os.chdir(tmp_path)
        assert cli._sync() == 1
        assert "Error" in capsys.readouterr().err

    def test_error_when_source_root_missing(self, tmp_path, capsys):
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent(
                """\
                [project]
                name = "demo"

                [tool.uncoded]
                source-roots = ["nope"]
                """
            )
        )
        os.chdir(tmp_path)
        assert cli._sync() == 1
        assert "Error" in capsys.readouterr().err


class TestSyncCheckMode:
    def test_returns_one_and_does_not_write_on_empty_repo(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")

        assert cli._sync(check=True) == 1
        # No artifacts written.
        assert not (tmp_path / ".uncoded").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_returns_zero_when_index_is_up_to_date(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()
        assert cli._sync(check=True) == 0

    def test_returns_one_when_source_changes_after_sync(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()
        # Signature changed: stub and namespace map are now stale.
        (tmp_path / "src" / "foo.py").write_text("def hello(name: str) -> str: pass\n")
        stub = tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi"
        stub_before = stub.read_text()

        assert cli._sync(check=True) == 1
        # Stale content is preserved — check mode must not mutate.
        assert stub.read_text() == stub_before

    def test_returns_one_when_source_file_deleted(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        (tmp_path / "src" / "bar.py").write_text("def goodbye(): pass\n")
        cli._sync()

        (tmp_path / "src" / "bar.py").unlink()
        assert cli._sync(check=True) == 1
        # Orphan stub must still be present after check.
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "bar.pyi").exists()

    def test_returns_one_when_instruction_file_drifts(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()

        # User edits CLAUDE.md navigation section by hand.
        claude = tmp_path / "CLAUDE.md"
        claude.write_text(claude.read_text().replace("uncoded", "scrambled"))
        claude_before = claude.read_text()

        assert cli._sync(check=True) == 1
        assert claude.read_text() == claude_before

    def test_error_still_returns_one(self, tmp_path, capsys):
        # Config error: check mode should report non-zero the same as apply mode.
        os.chdir(tmp_path)
        assert cli._sync(check=True) == 1
        assert "Error" in capsys.readouterr().err


class TestMainDispatch:
    def test_sync_subcommand_runs_in_apply_mode(self, tmp_path, monkeypatch):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        monkeypatch.setattr(sys, "argv", ["uncoded", "sync"])

        assert cli.main() == 0
        assert (tmp_path / ".uncoded" / "namespace.yaml").exists()

    def test_check_subcommand_runs_in_check_mode(self, tmp_path, monkeypatch):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        monkeypatch.setattr(sys, "argv", ["uncoded", "check"])

        assert cli.main() == 1
        # No artifacts written in check mode.
        assert not (tmp_path / ".uncoded").exists()

    def test_check_subcommand_returns_zero_on_fresh_index(self, tmp_path, monkeypatch):
        _init_repo(tmp_path)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()

        monkeypatch.setattr(sys, "argv", ["uncoded", "check"])
        assert cli.main() == 0

    def test_setup_subcommand(self, tmp_path, monkeypatch):
        _init_repo(tmp_path)
        monkeypatch.setattr(sys, "argv", ["uncoded", "setup"])
        assert cli.main() == 0
        assert (tmp_path / ".mcp.json").exists()

    def test_no_subcommand_is_an_error(self, tmp_path, monkeypatch):
        # Argparse enforces subparsers.required=True and exits with code 2
        # when no subcommand is given. This keeps the CLI honest: there is
        # no silent default, so every invocation names its operation.
        _init_repo(tmp_path)
        monkeypatch.setattr(sys, "argv", ["uncoded"])
        with pytest.raises(SystemExit):
            cli.main()

    def test_unknown_subcommand_is_an_error(self, tmp_path, monkeypatch):
        _init_repo(tmp_path)
        monkeypatch.setattr(sys, "argv", ["uncoded", "nonsense"])
        with pytest.raises(SystemExit):
            cli.main()
