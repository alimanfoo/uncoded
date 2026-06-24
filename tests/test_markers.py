"""Marker completeness: every generated-artefact family carries GENERATED_MARKER."""

from uncoded.docs_map import render_docs_map
from uncoded.markers import GENERATED_MARKER
from uncoded.namespace_map import render_map
from uncoded.skill import SKILLS, _render_content
from uncoded.stubs import StubModule, render_stub


class TestMarkerCompleteness:
    def test_namespace_map_carries_marker(self):
        assert GENERATED_MARKER in render_map({})

    def test_docs_map_carries_marker(self):
        assert GENERATED_MARKER in render_docs_map({})

    def test_stub_carries_marker(self):
        assert GENERATED_MARKER in render_stub(StubModule(rel_path="x.py"))

    def test_skill_carries_marker(self):
        assert GENERATED_MARKER in _render_content(skill=SKILLS[0])
