# src/uncoded/extract.py

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

def _property_kind(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Classify a method by its property-related decorators."""
    ...

def _assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    """Return the single-name target of an assignment, or None if not a simple name."""
    ...

def extract_module(source: str, rel_path: str) -> ModuleInfo:
    """Parse Python source and extract classes, functions, and constants."""
    ...

def iter_source_files(source_root: Path, base: Path | None) -> Iterator[tuple[str, str]]:
    """Yield (source_text, rel_path) for every Python file under *source_root*."""
    ...

def walk_source(source_root: Path, base: Path | None) -> list[ModuleInfo]:
    """Walk a source root and extract symbols from all Python files."""
    ...

class ClassInfo:
    """A class with its attributes and methods."""

    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)

class ModuleInfo:
    """Symbols found in a single Python module."""

    rel_path: str
    constants: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
