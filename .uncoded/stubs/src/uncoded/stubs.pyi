# src/uncoded/stubs.py

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from uncoded.extract import is_public, iter_source_files

def _first_sentence(node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module) -> str | None:  # L55-66
    """Return the first sentence of a node's docstring, or None."""
    ...

def _extract_params(args: ast.arguments) -> list[StubParam]:  # L69-97
    """Extract parameters from a function argument node, without defaults."""
    ...

def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> StubFunction:  # L100-112
    """Build a StubFunction from a function or method AST node."""
    ...

def _extract_class(node: ast.ClassDef) -> StubClass:  # L115-140
    """Build a StubClass from a class AST node."""
    ...

def extract_stub(source: str, rel_path: str) -> StubModule:  # L143-158
    """Parse Python source and extract all symbols with their signatures and line ranges."""
    ...

def _render_param(p: StubParam) -> str:  # L161-167
    """Render a single parameter as a string for a function signature."""
    ...

def _render_function(func: StubFunction, indent: str) -> list[str]:  # L170-181
    """Render a function or method as stub lines, with an optional indent for methods."""
    ...

def render_stub(module: StubModule) -> str:  # L184-217
    """Render a StubModule as a .pyi file string."""
    ...

def _generate_stubs(source_root: Path) -> dict[Path, str]:  # L220-231
    """Return a mapping from stub relative paths to rendered stub content."""
    ...

def build_stubs(source_root: Path, output_dir: Path) -> None:  # L237-243
    """Write stub files for all symbols under source_root."""
    ...

class StubParam:  # L12-16
    """A function parameter with name and optional type annotation."""

    name: str
    annotation: str | None

class StubFunction:  # L20-29
    """A function or method with its signature and line range."""

    name: str
    params: list[StubParam]
    return_annotation: str | None
    docstring_excerpt: str | None
    start_line: int
    end_line: int
    is_async: bool

class StubClass:  # L33-42
    """A class with its members and line range."""

    name: str
    bases: list[str]
    docstring_excerpt: str | None
    start_line: int
    end_line: int
    attributes: list[StubParam]
    methods: list[StubFunction]

class StubModule:  # L46-52
    """All symbols extracted from a single Python module."""

    rel_path: str
    imports: list[str]
    classes: list[StubClass]
    functions: list[StubFunction]
