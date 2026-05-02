from pathlib import Path

from uncoded.instruction_files import (
    MARKER_END,
    MARKER_START,
    generate_section,
    sync_instruction_file,
)


class TestGenerateSection:
    def test_contains_markers(self):
        section = generate_section()
        assert MARKER_START in section
        assert MARKER_END in section

    def test_markers_in_order(self):
        section = generate_section()
        assert section.index(MARKER_START) < section.index(MARKER_END)

    def test_ends_with_newline(self):
        assert generate_section().endswith("\n")


class TestSyncInstructionFile:
    def test_creates_file_if_missing(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(path)
        assert path.exists()
        assert generate_section() in path.read_text()

    def test_appends_to_existing_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text("# My Project\n\nSome content.\n")
        sync_instruction_file(path)
        content = path.read_text()
        assert "# My Project" in content
        assert generate_section() in content

    def test_replaces_existing_section(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        old_section = f"{MARKER_START}\nold content\n{MARKER_END}\n"
        path.write_text(f"# My Project\n\n{old_section}")
        sync_instruction_file(path)
        content = path.read_text()
        assert "old content" not in content
        assert generate_section() in content
        assert "# My Project" in content

    def test_preserves_content_after_section(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        old_section = f"{MARKER_START}\nold\n{MARKER_END}\n"
        path.write_text(f"{old_section}\n## Other section\n")
        sync_instruction_file(path)
        content = path.read_text()
        assert "## Other section" in content

    def test_idempotent(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(path)
        first = path.read_text()
        sync_instruction_file(path)
        assert path.read_text() == first

    def test_returns_true_on_first_write(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        assert sync_instruction_file(path) is True

    def test_returns_false_when_clean(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(path)
        assert sync_instruction_file(path) is False


class TestSyncInstructionFileCheckMode:
    def test_does_not_create_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        changed = sync_instruction_file(path, check=True)
        assert changed is True
        assert not path.exists()

    def test_does_not_update_existing_file(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        path.write_text("# My Project\n\nSome content.\n")
        original = path.read_text()
        changed = sync_instruction_file(path, check=True)
        assert changed is True
        assert path.read_text() == original

    def test_reports_no_change_when_clean(self, tmp_path):
        path = tmp_path / "CLAUDE.md"
        sync_instruction_file(path)
        changed = sync_instruction_file(path, check=True)
        assert changed is False


class TestSyncInstructionFileRootAnchor:
    def test_root_anchors_create_independent_of_cwd(self, tmp_path, monkeypatch):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("CLAUDE.md")
        changed = sync_instruction_file(rel, root=tmp_path)
        assert changed is True
        assert (tmp_path / rel).exists()
        assert generate_section() in (tmp_path / rel).read_text()
        assert not (sub / rel).exists()

    def test_root_anchors_update_of_existing_file(self, tmp_path, monkeypatch):
        sub = tmp_path / "subdir"
        sub.mkdir()
        monkeypatch.chdir(sub)

        rel = Path("CLAUDE.md")
        (tmp_path / rel).write_text("# My Project\n\nSome content.\n")

        changed = sync_instruction_file(rel, root=tmp_path)
        assert changed is True
        content = (tmp_path / rel).read_text()
        assert "# My Project" in content
        assert generate_section() in content
