"""End-to-end tests for the uncoded CLI.

These exercise :func:`cli._sync` (and :func:`cli.main` for subcommand
dispatch) on a real filesystem. The sister modules have their own unit
tests; this suite covers the orchestration and the ``check`` exit-code
contract.
"""

import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

from uncoded import cli
from uncoded.skill import SKILL_OUTPUTS


def _init_repo(tmp_path, monkeypatch, source_roots=("src",)):
    """Set up a minimal repo: pyproject.toml + source root + chdir.

    Uses ``monkeypatch.chdir`` (rather than bare ``os.chdir``) so cwd is
    restored on teardown — including when the test fails — preventing
    cwd leakage into subsequent unrelated tests.
    """
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
    monkeypatch.chdir(tmp_path)


class TestSyncApplyMode:
    def test_writes_namespace_map_stubs_and_instruction_file(
        self, tmp_path, monkeypatch
    ):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")

        assert cli._sync() == 0
        assert (tmp_path / ".uncoded" / "namespace.yaml").exists()
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        for skill_path in SKILL_OUTPUTS:
            assert (tmp_path / skill_path).exists()

    def test_idempotent_second_run(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
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

    def test_dedupes_when_claude_md_is_symlink_to_agents_md(
        self, tmp_path, monkeypatch, capsys
    ):
        # When CLAUDE.md is a symlink to AGENTS.md, both configured
        # instruction paths point to the same inode. Sync should process
        # the file once and report it under its canonical (resolved)
        # name, not iterate twice with asymmetric output.
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        agents = tmp_path / "AGENTS.md"
        agents.write_text("")
        (tmp_path / "CLAUDE.md").symlink_to(agents)

        assert cli._sync() == 0

        # The section is written through the symlink to AGENTS.md.
        assert "<!-- uncoded:start -->" in agents.read_text()

        # Exactly one user-facing line for the instruction file, naming
        # the canonical AGENTS.md.
        instruction_lines = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.endswith("AGENTS.md") or line.endswith("CLAUDE.md")
        ]
        assert instruction_lines == ["Updated AGENTS.md"]

    def test_instruction_file_outside_project_uses_absolute_path(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        (project / "src").mkdir()
        (project / "pyproject.toml").write_text(
            textwrap.dedent(
                """\
                [project]
                name = "demo"

                [tool.uncoded]
                source-roots = ["src"]
                instruction-files = ["../outside.md"]
                """
            )
        )
        monkeypatch.chdir(project)

        assert cli._sync() == 0

        outside_file = tmp_path / "outside.md"
        assert outside_file.exists()
        assert "<!-- uncoded:start -->" in outside_file.read_text()

    def test_error_when_no_pyproject_toml(self, tmp_path, monkeypatch, capsys):
        # Pins the problem statement, the recovery hint pointing at
        # [tool.uncoded] source-roots, and the absence of any absolute
        # path leak (this site's message has no path today; pinning
        # the absence guards against future regressions).
        monkeypatch.chdir(tmp_path)

        assert cli._sync() == 1

        err = capsys.readouterr().err
        assert "Error: No pyproject.toml found." in err
        assert "Create one with a [tool.uncoded] source-roots entry." in err
        assert str(tmp_path) not in err

    def test_error_when_source_root_missing(self, tmp_path, monkeypatch, capsys):
        # The message must (a) report the source-root path as the user
        # typed it in [tool.uncoded] source-roots, not the resolved
        # absolute path (which leaks the developer's filesystem layout),
        # and (b) include a recovery hint pointing at the config key.
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
        monkeypatch.chdir(tmp_path)

        assert cli._sync() == 1

        err = capsys.readouterr().err
        assert "Error: source root nope is not a directory." in err
        assert "Check [tool.uncoded] source-roots in pyproject.toml." in err
        assert str(tmp_path) not in err

    def test_error_when_uncoded_section_missing(self, tmp_path, monkeypatch, capsys):
        # User has pyproject.toml but no [tool.uncoded] section. The
        # message must (a) not surface the KeyError quoting artefact —
        # historically `Error: 'No ...'` with literal single quotes —
        # and (b) include a recovery hint case-specific to this state
        # ("Add [tool.uncoded] source-roots to configure"), because the
        # user has a pyproject.toml but lacks the section.
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
        monkeypatch.chdir(tmp_path)

        assert cli._sync() == 1

        err = capsys.readouterr().err
        assert (
            "Error: No [tool.uncoded] source-roots found in pyproject.toml. "
            "Add [tool.uncoded] source-roots to configure." in err
        )
        # No literal single-quote wrapping from KeyError.__str__.
        assert "Error: 'No" not in err

    def test_skip_warning_emitted_once_per_broken_file(
        self, tmp_path, monkeypatch, capsys
    ):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "good.py").write_text("def hello(): pass\n")
        (tmp_path / "src" / "broken.py").write_text("def bad(:\n")

        assert cli._sync() == 0

        skip_warnings = [
            line
            for line in capsys.readouterr().err.splitlines()
            if "skipping" in line and "broken.py" in line
        ]
        assert len(skip_warnings) == 1
        assert skip_warnings[0].startswith("warning: skipping src/broken.py")
        assert "SyntaxError" in skip_warnings[0]
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "good.pyi").exists()

    def test_anchors_reads_and_writes_at_project_root_when_cwd_is_subdir(
        self, tmp_path, monkeypatch
    ):
        # Running from a subdirectory of the project must produce
        # artefacts at the project root, not under the subdirectory.
        # Reads (source files, pyproject) anchor at project_root; writes
        # (namespace, stubs, instruction file, skill files) do too.
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent(
                """\
                [project]
                name = "demo"

                [tool.uncoded]
                source-roots = ["src"]
                """
            )
        )
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        monkeypatch.chdir(tmp_path / "src")

        assert cli._sync(start=tmp_path) == 0

        # Reads anchored: namespace map references the project-relative
        # source path, not a subdir-relative one.
        namespace_path = tmp_path / ".uncoded" / "namespace.yaml"
        assert namespace_path.exists()
        content = namespace_path.read_text()
        assert "src/:" in content
        assert "foo.py:" in content

        # Writes anchored: every artefact lands at project_root, never
        # under the subdirectory cwd.
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi").exists()
        assert (tmp_path / "CLAUDE.md").exists()
        for skill_path in SKILL_OUTPUTS:
            assert (tmp_path / skill_path).exists()
        assert not (tmp_path / "src" / ".uncoded").exists()
        assert not (tmp_path / "src" / "CLAUDE.md").exists()
        for skill_path in SKILL_OUTPUTS:
            assert not (tmp_path / "src" / skill_path).exists()

    def test_artefacts_match_when_run_from_subdir_vs_project_root(
        self, tmp_path, monkeypatch
    ):
        # Behavioural acceptance for GH84: identical artefacts in
        # identical locations whether sync runs from the project root
        # or from a subdirectory.
        def _mk_repo(under: Path) -> None:
            (under / "pyproject.toml").write_text(
                textwrap.dedent(
                    """\
                    [project]
                    name = "demo"

                    [tool.uncoded]
                    source-roots = ["src"]
                    """
                )
            )
            (under / "src").mkdir()
            (under / "src" / "foo.py").write_text("def hello(): pass\n")

        from_root = tmp_path / "from_root"
        from_subdir = tmp_path / "from_subdir"
        from_root.mkdir()
        from_subdir.mkdir()
        _mk_repo(from_root)
        _mk_repo(from_subdir)

        monkeypatch.chdir(from_root)
        assert cli._sync() == 0

        monkeypatch.chdir(from_subdir / "src")
        assert cli._sync() == 0

        relpaths = [
            Path(".uncoded/namespace.yaml"),
            Path(".uncoded/stubs/src/foo.pyi"),
            Path("CLAUDE.md"),
            *SKILL_OUTPUTS,
        ]
        for rel in relpaths:
            assert (from_root / rel).read_text() == (from_subdir / rel).read_text(), (
                f"artefact differs at {rel}"
            )


class TestSyncCheckMode:
    def test_returns_one_and_does_not_write_on_empty_repo(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")

        assert cli._sync(check=True) == 1
        # No artifacts written.
        assert not (tmp_path / ".uncoded").exists()
        assert not (tmp_path / "CLAUDE.md").exists()

    def test_returns_zero_when_index_is_up_to_date(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()
        assert cli._sync(check=True) == 0

    def test_returns_one_when_source_changes_after_sync(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()
        # Signature changed: stub and namespace map are now stale.
        (tmp_path / "src" / "foo.py").write_text("def hello(name: str) -> str: pass\n")
        stub = tmp_path / ".uncoded" / "stubs" / "src" / "foo.pyi"
        stub_before = stub.read_text()

        assert cli._sync(check=True) == 1
        # Stale content is preserved — check mode must not mutate.
        assert stub.read_text() == stub_before

    def test_returns_one_when_source_file_deleted(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        (tmp_path / "src" / "bar.py").write_text("def goodbye(): pass\n")
        cli._sync()

        (tmp_path / "src" / "bar.py").unlink()
        assert cli._sync(check=True) == 1
        # Orphan stub must still be present after check.
        assert (tmp_path / ".uncoded" / "stubs" / "src" / "bar.pyi").exists()

    def test_returns_one_when_instruction_file_drifts(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()

        # User edits CLAUDE.md navigation section by hand.
        claude = tmp_path / "CLAUDE.md"
        claude.write_text(claude.read_text().replace("uncoded", "scrambled"))
        claude_before = claude.read_text()

        assert cli._sync(check=True) == 1
        assert claude.read_text() == claude_before

    def test_dedupes_when_claude_md_is_symlink_to_agents_md(
        self, tmp_path, monkeypatch, capsys
    ):
        # Same symlink-dedup contract as apply mode, but in the freshness
        # gate. With CLAUDE.md a symlink to AGENTS.md, check mode must
        # report the instruction file once under its canonical AGENTS.md
        # name — asymmetric reporting here would let CI miss what apply
        # mode would do.
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        agents = tmp_path / "AGENTS.md"
        agents.write_text("")
        (tmp_path / "CLAUDE.md").symlink_to(agents)

        assert cli._sync(check=True) == 1

        # Check mode must not mutate — the symlinked file is still empty.
        assert agents.read_text() == ""

        # Exactly one user-facing line for the instruction file, naming
        # the canonical AGENTS.md.
        instruction_lines = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.endswith("AGENTS.md") or line.endswith("CLAUDE.md")
        ]
        assert instruction_lines == ["Would update AGENTS.md"]

    def test_error_still_returns_one(self, tmp_path, monkeypatch, capsys):
        # Config error: check mode should report non-zero the same as apply mode.
        monkeypatch.chdir(tmp_path)
        assert cli._sync(check=True) == 1
        assert "Error" in capsys.readouterr().err


class TestMainDispatch:
    def test_sync_subcommand_runs_in_apply_mode(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        monkeypatch.setattr(sys, "argv", ["uncoded", "sync"])

        assert cli.main() == 0
        assert (tmp_path / ".uncoded" / "namespace.yaml").exists()

    def test_check_subcommand_runs_in_check_mode(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        monkeypatch.setattr(sys, "argv", ["uncoded", "check"])

        assert cli.main() == 1
        # No artifacts written in check mode.
        assert not (tmp_path / ".uncoded").exists()

    def test_check_subcommand_returns_zero_on_fresh_index(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def hello(): pass\n")
        cli._sync()

        monkeypatch.setattr(sys, "argv", ["uncoded", "check"])
        assert cli.main() == 0

    def test_no_subcommand_is_an_error(self, tmp_path, monkeypatch):
        # Argparse enforces subparsers.required=True and exits with code 2
        # when no subcommand is given. This keeps the CLI honest: there is
        # no silent default, so every invocation names its operation.
        _init_repo(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["uncoded"])
        with pytest.raises(SystemExit):
            cli.main()

    def test_unknown_subcommand_is_an_error(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["uncoded", "nonsense"])
        with pytest.raises(SystemExit):
            cli.main()


class TestBodyCommand:
    def test_happy_path_dispatch(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def fn():\n    pass\n")
        argv = ["uncoded", "body", "fn", "--in", "src/foo.py"]
        monkeypatch.setattr(sys, "argv", argv)

        assert cli.main() == 0
        assert capsys.readouterr().out == "def fn():\n    pass\n"

    def test_class_method_form(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text(
            "class Dog:\n    def bark(self):\n        pass\n"
        )

        assert cli._body(name_path="Dog/bark", in_path="src/foo.py") == 0
        assert capsys.readouterr().out == "    def bark(self):\n        pass\n"

    def test_symbol_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def other(): pass\n")

        assert cli._body(name_path="missing", in_path="src/foo.py") == 1

        err = capsys.readouterr().err
        assert "missing" in err
        assert "foo.py" in err

    def test_file_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)

        assert cli._body(name_path="fn", in_path="src/nonexistent.py") == 1
        assert "nonexistent.py" in capsys.readouterr().err

    def test_syntax_error_exits_one(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def broken(:\n")

        assert cli._body(name_path="broken", in_path="src/foo.py") == 1
        assert "foo.py" in capsys.readouterr().err

    def test_works_without_project_root(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def fn():\n    pass\n")

        assert cli._body(name_path="fn", in_path="m.py") == 0
        assert capsys.readouterr().out == "def fn():\n    pass\n"

    def test_in_path_resolves_relative_to_cwd(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def fn():\n    pass\n")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        assert cli._body(name_path="fn", in_path="../src/foo.py") == 0
        assert capsys.readouterr().out == "def fn():\n    pass\n"

    def test_stdout_is_exact_body(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        body = "def compute(x: int) -> int:\n    return x * 2\n"
        source = f"# header\n\n{body}\n# footer\n"
        (tmp_path / "src" / "foo.py").write_text(source)

        assert cli._body(name_path="compute", in_path="src/foo.py") == 0

        out, err = capsys.readouterr()
        assert out == body
        assert err == ""

    def test_unsupported_name_path_exits_one(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / "src" / "foo.py").write_text("def fn(): pass\n")

        assert cli._body(name_path="A/B/C", in_path="src/foo.py") == 1

        err = capsys.readouterr().err
        assert "Error:" in err
        assert "'name'" in err
        assert "'Class/member'" in err

    def test_missing_in_flag_exits_with_two(self, tmp_path, monkeypatch, capsys):
        _init_repo(tmp_path, monkeypatch)
        monkeypatch.setattr(sys, "argv", ["uncoded", "body", "fn"])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 2
        assert capsys.readouterr().err != ""


class TestRefsCommand:
    def test_happy_path_dispatch(self, tmp_path, monkeypatch, capsys):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text("from pkg.a import foo\nfoo()\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["uncoded", "refs", "foo", "--in", "pkg/a.py"])

        assert cli.main() == 0
        out = capsys.readouterr().out
        assert "pkg/b.py:2:1" in out

    def test_class_method_form(self, tmp_path, monkeypatch, capsys):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text(
            textwrap.dedent("""\
                class Dog:
                    def bark(self):
                        pass
            """)
        )
        (pkg / "b.py").write_text(
            "from pkg.a import Dog\nd = Dog()\nd.bark()\nd.bark()\n"
        )
        monkeypatch.chdir(tmp_path)

        assert cli._refs(name_path="Dog/bark", in_path="pkg/a.py") == 0
        out = capsys.readouterr().out
        lines = out.strip().splitlines()
        assert len(lines) == 2
        assert all("pkg/b.py" in line for line in lines)

    def test_symbol_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def other(): pass\n")

        assert cli._refs(name_path="missing", in_path="m.py") == 1
        err = capsys.readouterr().err
        assert "missing" in err
        assert "m.py" in err

    def test_file_not_found_exits_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)

        assert cli._refs(name_path="fn", in_path="nonexistent.py") == 1
        assert "nonexistent.py" in capsys.readouterr().err

    def test_syntax_error_exits_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def broken(:\n")

        assert cli._refs(name_path="broken", in_path="m.py") == 1
        assert "m.py" in capsys.readouterr().err

    def test_works_without_project_root(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.py").write_text("def foo():\n    pass\n")
        (tmp_path / "b.py").write_text("from a import foo\nfoo()\n")

        assert cli._refs(name_path="foo", in_path="a.py") == 0
        assert capsys.readouterr().err == ""

    def test_in_path_resolves_relative_to_cwd(self, tmp_path, monkeypatch, capsys):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    pass\n")
        (pkg / "b.py").write_text("from pkg.a import foo\nfoo()\n")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        assert cli._refs(name_path="foo", in_path="../pkg/a.py") == 0
        assert capsys.readouterr().err == ""

    def test_unsupported_name_path_exits_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def fn(): pass\n")

        assert cli._refs(name_path="A/B/C", in_path="m.py") == 1
        err = capsys.readouterr().err
        assert "Error:" in err
        assert "'name'" in err
        assert "'Class/member'" in err

    def test_missing_in_flag_exits_with_two(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["uncoded", "refs", "fn"])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 2
        assert capsys.readouterr().err != ""

    def test_zero_references_exits_zero_with_empty_stdout(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def uncalled():\n    pass\n")

        assert cli._refs(name_path="uncalled", in_path="m.py") == 0
        out, err = capsys.readouterr()
        assert out == ""
        assert err == ""

    def test_multiple_references_prints_sorted(self, tmp_path, monkeypatch, capsys):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "t"\n')
        (pkg / "a.py").write_text("def foo():\n    return 42\n")
        (pkg / "b.py").write_text(
            "from pkg.a import foo\nresult = foo()\nother = foo()\n"
        )
        monkeypatch.chdir(tmp_path)

        assert cli._refs(name_path="foo", in_path="pkg/a.py") == 0
        lines = capsys.readouterr().out.strip().splitlines()
        assert len(lines) == 2
        assert lines[0] == "pkg/b.py:2:10"
        assert lines[1] == "pkg/b.py:3:9"

    def test_lsp_failure_exits_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "m.py").write_text("def foo(): pass\n")

        with mock.patch("uncoded.cli.find_refs", side_effect=RuntimeError("ty error")):
            assert cli._refs(name_path="foo", in_path="m.py") == 1

        assert "ty error" in capsys.readouterr().err
