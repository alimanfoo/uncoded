"""Marker completeness: the maps, the stubs and the skills carry GENERATED_MARKER."""

from uncoded.docs_map import render_docs_map
from uncoded.extract import PythonFile
from uncoded.markers import GENERATED_MARKER
from uncoded.namespace_map import render_namespace_map
from uncoded.skill import _SKILLS, _render_content
from uncoded.stubs import _render_stub


class TestMarkerCompleteness:
    def test_namespace_map_carries_marker(self):
        assert GENERATED_MARKER in render_namespace_map(mapping={})

    def test_docs_map_carries_marker(self):
        assert GENERATED_MARKER in render_docs_map(mapping={})

    def test_stub_carries_marker(self):
        assert GENERATED_MARKER in _render_stub(python_file=PythonFile(rel_path="x.py"))

    def test_skill_carries_marker(self):
        assert GENERATED_MARKER in _render_content(skill=_SKILLS[0])
