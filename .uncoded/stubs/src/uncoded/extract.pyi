# src/uncoded/extract.py

import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

def property_kind(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    ...

def _assign_target_name(node: ast.Assign | ast.AnnAssign) -> str | None:
    ...

def extract_module(source: str, rel_path: str) -> ModuleInfo:
    ...

def iter_source_files(source_root: Path, project_root: Path) -> Iterator[tuple[str, str]]:
    ...

def extract_modules(files: Iterable[tuple[str, str]]) -> list[ModuleInfo]:
    ...

class ClassInfo:
    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)

class ModuleInfo:
    rel_path: str
    constants: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
