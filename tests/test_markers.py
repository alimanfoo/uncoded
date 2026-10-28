"""Marker completeness: every kind of generated file carries GENERATED_MARKER."""

from pathlib import Path

from uncoded.cli import _sync
from uncoded.config import Config
from uncoded.docs_map import render_docs_map
from uncoded.markers import GENERATED_MARKER
from uncoded.namespace_map import render_map
from uncoded.skill import SKILLS, _render_content
from uncoded.stubs import StubModule, render_stub


class TestMarkerCompleteness:
    def test_namespace_map_carries_marker(self):
        assert GENERATED_MARKER in render_map(namespace={})

    def test_docs_map_carries_marker(self):
        assert GENERATED_MARKER in render_docs_map(mapping={})

    def test_stub_carries_marker(self):
        assert GENERATED_MARKER in render_stub(module=StubModule(rel_path="x.py"))

    def test_skill_carries_marker(self):
        assert GENERATED_MARKER in _render_content(skill=SKILLS[0])

    def test_gitignore_carries_marker(self, *, tmp_path):
        (tmp_path / "README.md").write_text("# Title\n", encoding="utf-8")
        _sync(
            config=Config(
                configuration_file=tmp_path / ".uncoded.toml",
                source_roots=[],
                doc_roots=[Path("README.md")],
                required_version=None,
            )
        )
        gitignore = tmp_path / ".uncoded" / ".gitignore"
        assert GENERATED_MARKER in gitignore.read_text(encoding="utf-8")
