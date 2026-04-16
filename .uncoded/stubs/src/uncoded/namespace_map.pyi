# src/uncoded/namespace_map.py

from pathlib import Path
import yaml
from uncoded.extract import ModuleInfo

HEADER = ...  # L9-20

def build_map(modules: list[ModuleInfo]) -> dict:  # L38-74
    """Build a nested dict representing the namespace."""
    ...

def render_map(namespace: dict) -> str:  # L77-85
    """Render a namespace map dict as a YAML string with an explanatory header."""
    ...

class _CleanDumper(yaml.SafeDumper):  # L23-28
    """YAML dumper that indents list items and suppresses 'null' values."""

    def increase_indent(self, flow, indentless):  # L26-28
        """Force list items to be indented relative to their parent key."""
        ...
