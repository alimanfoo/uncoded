# src/uncoded/extract.py

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

_DUNDER_PUBLIC = frozenset({'__all__', '__version__'})  # L29

def is_public(name: str) -> bool:  # L32-36
    """A name is public if it has no leading underscore (or is a public dunder)."""
    ...

def _property_kind(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:  # L39-52
    """Classify a method by its property-related decorators."""
    ...

def _assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:  # L55-63
    """Return the single-name target of an assignment, or None if not a simple name."""
    ...

def extract_module(source: str, rel_path: str) -> ModuleInfo:  # L66-113
    """Parse Python source and extract public classes, functions, and constants."""
    ...

def iter_source_files(source_root: Path, base: Path | None) -> Iterator[tuple[str, str]]:  # L116-143
    """Yield (source_text, rel_path) for each candidate Python file."""
    ...

def walk_source(source_root: Path, base: Path | None) -> list[ModuleInfo]:  # L146-167
    """Walk a source root and extract public symbols from all packages."""
    ...

class ClassInfo:  # L10-15
    """A public class with its public attributes and methods."""

    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)

class ModuleInfo:  # L19-25
    """Public symbols found in a single Python module."""

    rel_path: str
    constants: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
