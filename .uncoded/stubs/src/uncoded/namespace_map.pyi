# src/uncoded/namespace_map.py

from pathlib import Path
from uncoded.extract import ModuleInfo
from uncoded.yaml_tree import render_yaml_tree

HEADER = ...

def build_map(modules: list[ModuleInfo]) -> dict:
    ...

def render_map(namespace: dict) -> str:
    ...
