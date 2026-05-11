# src/uncoded/namespace_map.py

from pathlib import Path
import yaml
from uncoded.extract import ModuleInfo

HEADER = ...

def build_map(modules: list[ModuleInfo]) -> dict:
    ...

def render_map(namespace: dict) -> str:
    ...

class _CleanDumper(yaml.SafeDumper):
    def increase_indent(self, flow, indentless):
        ...
