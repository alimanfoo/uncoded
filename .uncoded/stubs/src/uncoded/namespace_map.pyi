# src/uncoded/namespace_map.py

"""Generate a YAML namespace map from extracted symbols."""

from pathlib import Path
import yaml
from uncoded.extract import ModuleInfo

HEADER = ...

def build_map(modules: list[ModuleInfo]) -> dict:
    """Build a nested dict representing the namespace."""
    ...

def render_map(namespace: dict) -> str:
    """Render a namespace map dict as a YAML string with an explanatory header."""
    ...

class _CleanDumper(yaml.SafeDumper):
    """YAML dumper that indents list items and suppresses 'null' values."""

    def increase_indent(self, flow, indentless):
        """Force list items to be indented relative to their parent key."""
        ...
