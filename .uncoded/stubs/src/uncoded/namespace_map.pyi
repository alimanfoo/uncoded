# src/uncoded/namespace_map.py

from pathlib import Path
import yaml
from uncoded.extract import ModuleInfo

def build_map(modules: list[ModuleInfo]) -> dict:  # L25-58
    """Build a nested dict representing the namespace."""
    ...

def render_map(namespace: dict) -> str:  # L61-68
    """Render a namespace map dict as a YAML string."""
    ...

class _CleanDumper(yaml.SafeDumper):  # L10-15
    """YAML dumper that indents list items and suppresses 'null' values."""

    def increase_indent(self, flow, indentless):  # L13-15
        """Force list items to be indented relative to their parent key."""
        ...
