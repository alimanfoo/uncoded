# src/uncoded/extract.py

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

def is_public(name: str) -> bool:  # L27-29
    """A name is public if it has no leading underscore."""
    ...

def extract_module(source: str, rel_path: str) -> ModuleInfo:  # L32-62
    """Parse Python source and extract public classes and functions."""
    ...

def iter_source_files(source_root: Path, base: Path | None) -> Iterator[tuple[str, str]]:  # L65-92
    """Yield (source_text, rel_path) for each candidate Python file."""
    ...

def walk_source(source_root: Path, base: Path | None) -> list[ModuleInfo]:  # L95-116
    """Walk a source root and extract public symbols from all packages."""
    ...

class ClassInfo:  # L10-15
    """A public class with its public attributes and methods."""

    name: str
    attributes: list[str]
    methods: list[str]

class ModuleInfo:  # L19-24
    """Public symbols found in a single Python module."""

    rel_path: str
    classes: list[ClassInfo]
    functions: list[str]
