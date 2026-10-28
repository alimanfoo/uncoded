from importlib.resources import files
from pathlib import Path

import pytest

import uncoded.skill as skill_module
from uncoded.markers import GENERATED_MARKER
from uncoded.skill import SKILL_ROOTS, SKILLS, Skill, agent_instructions, sync_skills

_REVIEW_SKILL = SKILLS[0]
_REVIEW_SKILL_FILE = Path(_REVIEW_SKILL.name) / "SKILL.md"


class TestSyncSkills:
    def test_skill_registry(self):
        names = [s.name for s in SKILLS]
        assert "uncoded-consistency-review" in names
        assert "uncoded-code-navigation" in names
        assert "uncoded-doc-navigation" in names
        assert _REVIEW_SKILL.name == "uncoded-consistency-review"
        assert _REVIEW_SKILL.gate == "source"
        code_nav = next(s for s in SKILLS if s.name == "uncoded-code-navigation")
        assert code_nav.gate == "source"
        doc_nav = next(s for s in SKILLS if s.name == "uncoded-doc-navigation")
        assert doc_nav.gate == "docs"
        assert [
            Path(".claude/skills"),
            Path(".agents/skills"),
        ] == SKILL_ROOTS

    def test_writes_skill_files(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / _REVIEW_SKILL_FILE).exists()

    def test_creates_parent_directories(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / _REVIEW_SKILL_FILE.parent).is_dir()

    def test_content_has_frontmatter_and_body(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        skill = _REVIEW_SKILL
        content = (tmp_path / SKILL_ROOTS[0] / skill.name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert content.startswith(f"---\nname: {skill.name}\n")
        assert skill.description in content
        # Renderer owns the blank-line separator; body follows directly after it.
        body = (
            (files("uncoded") / skill.body_file)
            .read_text(encoding="utf-8")
            .lstrip("\n")
        )
        assert content.endswith("\n\n" + body)

    def test_renderer_supplies_separator_for_body_without_leading_newline(
        self, *, monkeypatch, tmp_path
    ):
        # The renderer must insert exactly one blank line even when the body
        # file has no leading newline.
        (tmp_path / "test.md").write_text("# Body\n", encoding="utf-8")
        monkeypatch.setattr(skill_module, "files", lambda pkg: tmp_path)
        test_skill = Skill(
            name="test", description="A test.", body_file="test.md", gate="source"
        )
        content = skill_module._render_content(skill=test_skill)
        assert f"<!-- {GENERATED_MARKER} -->" in content
        assert content.endswith("\n\n# Body\n")

    def test_content_has_provenance_marker(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        skill = _REVIEW_SKILL
        content = (tmp_path / SKILL_ROOTS[0] / skill.name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        # Marker is present in the rendered file.
        assert f"<!-- {GENERATED_MARKER} -->" in content
        # Marker follows the closing frontmatter ---, not inside it.
        frontmatter_close = content.index("\n---\n", 4) + 5
        assert f"<!-- {GENERATED_MARKER} -->" in content[frontmatter_close:]

    def test_returns_change_count_on_first_write(self, *, tmp_path):
        result = sync_skills(
            source=True, docs=False, project_directory=tmp_path, check=False
        )
        assert result == 4

    def test_returns_zero_when_already_in_sync(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        assert (
            sync_skills(
                source=True, docs=False, project_directory=tmp_path, check=False
            )
            == 0
        )

    def test_idempotent(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        mtimes = [
            (tmp_path / root / _REVIEW_SKILL_FILE).stat().st_mtime_ns
            for root in SKILL_ROOTS
        ]
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        assert [
            (tmp_path / root / _REVIEW_SKILL_FILE).stat().st_mtime_ns
            for root in SKILL_ROOTS
        ] == mtimes

    def test_check_mode_does_not_write(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=True)
        for root in SKILL_ROOTS:
            assert not (tmp_path / root / _REVIEW_SKILL_FILE).exists()

    def test_check_mode_reports_change_when_missing(self, *, tmp_path):
        assert (
            sync_skills(source=True, docs=False, project_directory=tmp_path, check=True)
            > 0
        )

    def test_check_mode_reports_no_change_when_in_sync(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        assert (
            sync_skills(source=True, docs=False, project_directory=tmp_path, check=True)
            == 0
        )

    @pytest.mark.parametrize("source", [True, False])
    def test_leaves_a_skill_of_the_users_own_in_place(self, *, tmp_path, source):
        # coherence-review was the skill's name before uncoded 2.0. A skill of
        # that name now belongs to the user, whichever roots the project has.
        own_paths = [
            tmp_path / root / "coherence-review" / "SKILL.md" for root in SKILL_ROOTS
        ]
        for path in own_paths:
            path.parent.mkdir(parents=True)
            path.write_text("the user's own skill\n", encoding="utf-8")

        sync_skills(source=source, docs=False, project_directory=tmp_path, check=False)

        for path in own_paths:
            assert path.read_text(encoding="utf-8") == "the user's own skill\n"

    def test_source_false_removes_current_skill_files(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        assert (
            sync_skills(
                source=False, docs=False, project_directory=tmp_path, check=False
            )
            > 0
        )
        for root in SKILL_ROOTS:
            assert not (tmp_path / root / _REVIEW_SKILL_FILE).exists()

    def test_source_false_returns_zero_when_already_absent(self, *, tmp_path):
        assert (
            sync_skills(
                source=False, docs=False, project_directory=tmp_path, check=False
            )
            == 0
        )

    def test_source_false_check_mode_reports_without_removing(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        assert (
            sync_skills(
                source=False, docs=False, project_directory=tmp_path, check=True
            )
            > 0
        )
        for root in SKILL_ROOTS:
            assert (tmp_path / root / _REVIEW_SKILL_FILE).exists()

    def test_gate_unmet_removal_prunes_empty_directory(self, *, tmp_path):
        # After gate-not-met removal, the skill directory itself must be gone.
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        sync_skills(source=False, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (tmp_path / root / _REVIEW_SKILL_FILE.parent).exists()

    def test_pruning_skipped_when_directory_has_other_files(self, *, tmp_path):
        # If extra files remain after SKILL.md removal, leave the directory.
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            extra = tmp_path / root / _REVIEW_SKILL_FILE.parent / "extra.md"
            extra.write_text("extra\n", encoding="utf-8")
        sync_skills(source=False, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / _REVIEW_SKILL_FILE.parent).is_dir()
            assert not (tmp_path / root / _REVIEW_SKILL_FILE).exists()

    def test_docs_gate_builds_when_docs_true(self, *, tmp_path, monkeypatch):
        docs_skill = Skill(
            name="test-docs",
            description="Test docs skill.",
            body_file=_REVIEW_SKILL.body_file,
            gate="docs",
        )
        monkeypatch.setattr(skill_module, "SKILLS", [docs_skill])
        sync_skills(source=False, docs=True, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "test-docs" / "SKILL.md").exists()

    def test_docs_gate_skips_when_docs_false(self, *, tmp_path, monkeypatch):
        docs_skill = Skill(
            name="test-docs",
            description="Test docs skill.",
            body_file=_REVIEW_SKILL.body_file,
            gate="docs",
        )
        monkeypatch.setattr(skill_module, "SKILLS", [docs_skill])
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (tmp_path / root / "test-docs" / "SKILL.md").exists()

    def test_code_navigation_written_when_source_set(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-code-navigation" / "SKILL.md").exists()

    def test_code_navigation_not_written_when_source_absent(self, *, tmp_path):
        sync_skills(source=False, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-code-navigation" / "SKILL.md"
            ).exists()

    def test_doc_navigation_written_when_docs_set(self, *, tmp_path):
        sync_skills(source=False, docs=True, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-doc-navigation" / "SKILL.md").exists()

    def test_doc_navigation_not_written_when_docs_absent(self, *, tmp_path):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-doc-navigation" / "SKILL.md"
            ).exists()

    def test_doc_navigation_content_includes_orient_step(self, *, tmp_path):
        sync_skills(source=False, docs=True, project_directory=tmp_path, check=False)
        content = (
            tmp_path / SKILL_ROOTS[0] / "uncoded-doc-navigation" / "SKILL.md"
        ).read_text(encoding="utf-8")
        assert ".uncoded/docs.yaml" in content
        # Orient step must tell the agent to read the map before anything else.
        # Collapse whitespace so the check survives prose line-wrapping.
        assert "before any other tool call" in " ".join(content.split())


class TestSyncSkillsProjectRootAnchor:
    def test_project_directory_anchors_writes_independent_of_cwd(
        self, *, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)

        for root in SKILL_ROOTS:
            assert (tmp_path / root / _REVIEW_SKILL_FILE).exists()
            assert not (sub / root / _REVIEW_SKILL_FILE).exists()

    def test_project_directory_anchors_removal_independent_of_cwd(
        self, *, tmp_path, monkeypatch
    ):
        sync_skills(source=True, docs=False, project_directory=tmp_path, check=False)
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        sync_skills(source=False, docs=False, project_directory=tmp_path, check=False)

        for root in SKILL_ROOTS:
            assert not (tmp_path / root / _REVIEW_SKILL_FILE).exists()


class TestAgentInstructions:
    @pytest.mark.parametrize(
        ("source", "docs", "skill_names"),
        [
            (True, True, ["uncoded-code-navigation", "uncoded-doc-navigation"]),
            (True, False, ["uncoded-code-navigation"]),
            (False, True, ["uncoded-doc-navigation"]),
        ],
    )
    def test_loads_the_navigation_skill_of_each_kind_of_root(
        self, *, source, docs, skill_names
    ):
        lines = agent_instructions(source=source, docs=docs).splitlines()

        assert lines[:2] == ["## Before you start", ""]
        assert [line.split("`")[1] for line in lines[2:]] == skill_names
