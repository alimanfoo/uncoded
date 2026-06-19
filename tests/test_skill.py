from importlib.resources import files
from pathlib import Path

import uncoded.skill as skill_module
from uncoded.skill import SKILL_ROOTS, SKILLS, Skill, sync_skills


class TestSyncSkills:
    def test_skill_registry(self):
        names = [s.name for s in SKILLS]
        assert "uncoded-coherence-review" in names
        assert "uncoded-code-navigation" in names
        assert "uncoded-doc-navigation" in names
        coherence = next(s for s in SKILLS if s.name == "uncoded-coherence-review")
        assert coherence.gate == "code"
        assert "coherence-review" in coherence.legacy_names
        assert "uncoded-review" in coherence.legacy_names
        code_nav = next(s for s in SKILLS if s.name == "uncoded-code-navigation")
        assert code_nav.gate == "code"
        assert code_nav.legacy_names == ()
        doc_nav = next(s for s in SKILLS if s.name == "uncoded-doc-navigation")
        assert doc_nav.gate == "docs"
        assert doc_nav.legacy_names == ()
        assert [
            Path(".claude/skills"),
            Path(".agents/skills"),
        ] == SKILL_ROOTS

    def test_writes_skill_files(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-coherence-review" / "SKILL.md").exists()

    def test_creates_parent_directories(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-coherence-review").is_dir()

    def test_content_has_frontmatter_and_body(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        skill = SKILLS[0]
        content = (tmp_path / SKILL_ROOTS[0] / skill.name / "SKILL.md").read_text()
        assert content.startswith("---\nname: uncoded-coherence-review\n")
        assert skill.description in content
        # Renderer owns the blank-line separator; body follows directly after it.
        body = (
            (files("uncoded") / skill.body_file)
            .read_text(encoding="utf-8")
            .lstrip("\n")
        )
        assert content.endswith("\n\n" + body)

    def test_renderer_supplies_separator_for_body_without_leading_newline(
        self, monkeypatch
    ):
        # The renderer must insert exactly one blank line even when the body
        # file has no leading newline.
        class _FakeResource:
            def __truediv__(self, name: str) -> "_FakeResource":
                return self

            def read_text(self, encoding: str) -> str:
                return "# Body\n"

        monkeypatch.setattr(skill_module, "files", lambda pkg: _FakeResource())
        test_skill = Skill(
            name="test", description="A test.", body_file="test.md", gate="code"
        )
        content = skill_module._render_content(skill=test_skill)
        assert content.endswith("---\n\n# Body\n")

    def test_returns_change_count_on_first_write(self, tmp_path):
        # Two code-gated skills × two roots = 4 writes; doc-nav skipped (docs=False).
        result = sync_skills(
            source=True, docs=False, project_root=tmp_path, check=False
        )
        assert result == 4

    def test_returns_zero_when_already_in_sync(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        assert (
            sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
            == 0
        )

    def test_idempotent(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        mtimes = [
            (tmp_path / root / "uncoded-coherence-review" / "SKILL.md")
            .stat()
            .st_mtime_ns
            for root in SKILL_ROOTS
        ]
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        assert [
            (tmp_path / root / "uncoded-coherence-review" / "SKILL.md")
            .stat()
            .st_mtime_ns
            for root in SKILL_ROOTS
        ] == mtimes

    def test_check_mode_does_not_write(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=True)
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-coherence-review" / "SKILL.md"
            ).exists()

    def test_check_mode_reports_change_when_missing(self, tmp_path):
        assert (
            sync_skills(source=True, docs=False, project_root=tmp_path, check=True) > 0
        )

    def test_check_mode_reports_no_change_when_in_sync(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        assert (
            sync_skills(source=True, docs=False, project_root=tmp_path, check=True) == 0
        )

    def test_removes_legacy_skill_files(self, tmp_path):
        # Both legacy names — the old prefixed dir and the pre-rename name.
        legacy_paths = [
            tmp_path / root / legacy / "SKILL.md"
            for legacy in ("coherence-review", "uncoded-review")
            for root in SKILL_ROOTS
        ]
        for path in legacy_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("old skill\n")

        assert (
            sync_skills(source=True, docs=False, project_root=tmp_path, check=False) > 0
        )
        for path in legacy_paths:
            assert not path.exists()

    def test_check_mode_reports_legacy_files_without_removing(self, tmp_path):
        legacy_paths = [
            tmp_path / root / legacy / "SKILL.md"
            for legacy in ("coherence-review", "uncoded-review")
            for root in SKILL_ROOTS
        ]
        for path in legacy_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("old skill\n")

        assert (
            sync_skills(source=True, docs=False, project_root=tmp_path, check=True) > 0
        )
        for path in legacy_paths:
            assert path.exists()

    def test_source_false_removes_existing_skill_files(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-coherence-review" / "SKILL.md").exists()
        assert (
            sync_skills(source=False, docs=False, project_root=tmp_path, check=False)
            > 0
        )
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-coherence-review" / "SKILL.md"
            ).exists()

    def test_source_false_returns_zero_when_already_absent(self, tmp_path):
        assert (
            sync_skills(source=False, docs=False, project_root=tmp_path, check=False)
            == 0
        )

    def test_source_false_check_mode_reports_without_removing(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        assert (
            sync_skills(source=False, docs=False, project_root=tmp_path, check=True) > 0
        )
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-coherence-review" / "SKILL.md").exists()

    def test_docs_gate_builds_when_docs_true(self, tmp_path, monkeypatch):
        docs_skill = Skill(
            name="test-docs",
            description="Test docs skill.",
            body_file="coherence_review.md",
            gate="docs",
        )
        monkeypatch.setattr(skill_module, "SKILLS", [docs_skill])
        sync_skills(source=False, docs=True, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "test-docs" / "SKILL.md").exists()

    def test_docs_gate_skips_when_docs_false(self, tmp_path, monkeypatch):
        docs_skill = Skill(
            name="test-docs",
            description="Test docs skill.",
            body_file="coherence_review.md",
            gate="docs",
        )
        monkeypatch.setattr(skill_module, "SKILLS", [docs_skill])
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (tmp_path / root / "test-docs" / "SKILL.md").exists()

    def test_no_legacy_names_skips_legacy_removal(self, tmp_path, monkeypatch):
        # A skill with empty legacy_names should generate exactly 2 writes.
        no_legacy_skill = Skill(
            name="no-legacy",
            description="A skill with no legacy names.",
            body_file="coherence_review.md",
            gate="code",
        )
        monkeypatch.setattr(skill_module, "SKILLS", [no_legacy_skill])
        result = sync_skills(
            source=True, docs=False, project_root=tmp_path, check=False
        )
        assert result == 2

    def test_code_navigation_written_when_source_set(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-code-navigation" / "SKILL.md").exists()

    def test_code_navigation_not_written_when_source_absent(self, tmp_path):
        sync_skills(source=False, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-code-navigation" / "SKILL.md"
            ).exists()

    def test_doc_navigation_written_when_docs_set(self, tmp_path):
        sync_skills(source=False, docs=True, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-doc-navigation" / "SKILL.md").exists()

    def test_doc_navigation_not_written_when_docs_absent(self, tmp_path):
        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)
        for root in SKILL_ROOTS:
            assert not (
                tmp_path / root / "uncoded-doc-navigation" / "SKILL.md"
            ).exists()

    def test_doc_navigation_content_includes_orient_step(self, tmp_path):
        sync_skills(source=False, docs=True, project_root=tmp_path, check=False)
        content = (
            tmp_path / SKILL_ROOTS[0] / "uncoded-doc-navigation" / "SKILL.md"
        ).read_text()
        assert ".uncoded/docs.yaml" in content
        # Orient step must tell the agent to read the map before anything else.
        assert "session start" in content


class TestSyncSkillsProjectRootAnchor:
    def test_project_root_anchors_writes_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)

        for root in SKILL_ROOTS:
            assert (tmp_path / root / "uncoded-coherence-review" / "SKILL.md").exists()
            assert not (sub / root / "uncoded-coherence-review" / "SKILL.md").exists()

    def test_project_root_anchors_legacy_removal_independent_of_cwd(
        self, tmp_path, monkeypatch
    ):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        for root in SKILL_ROOTS:
            for legacy in ("coherence-review", "uncoded-review"):
                legacy_path = tmp_path / root / legacy / "SKILL.md"
                legacy_path.parent.mkdir(parents=True, exist_ok=True)
                legacy_path.write_text("old skill\n")

        sync_skills(source=True, docs=False, project_root=tmp_path, check=False)

        for root in SKILL_ROOTS:
            for legacy in ("coherence-review", "uncoded-review"):
                assert not (tmp_path / root / legacy / "SKILL.md").exists()
