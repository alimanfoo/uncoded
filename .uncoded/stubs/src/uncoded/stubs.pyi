# src/uncoded/stubs.py

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from uncoded.extract import _property_kind, iter_source_files

VALUE_WIDTH_CAP = 80  # L12
DEFAULT_STUBS_OUTPUT = Path('.uncoded/stubs')  # L370

def _first_sentence(node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module) -> str | None:  # L77-88
    """Return the first sentence of a node's docstring, or None."""
    ...

def _extract_params(args: ast.arguments) -> list[StubParam]:  # L91-123
    """Extract parameters from a function argument node, without defaults."""
    ...

def _line_range(start: int, end: int) -> str:  # L126-128
    """Render a line range: 'L<start>' if single-line, else 'L<start>-<end>'."""
    ...

def _render_value(value: ast.expr) -> str:  # L131-136
    """Render an expression as source, eliding to '...' if too long or multi-line."""
    ...

def _extract_assignment(node: ast.Assign | ast.AnnAssign | ast.TypeAlias) -> StubAssignment | None:  # L139-182
    """Build a StubAssignment from an assignment-style AST node."""
    ...

def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> StubFunction:  # L185-197
    """Build a StubFunction from a function or method AST node."""
    ...

def _property_attribute(node: ast.FunctionDef | ast.AsyncFunctionDef) -> StubAssignment:  # L200-211
    """Build a StubAssignment representing a @property as a class attribute."""
    ...

def _extract_class(node: ast.ClassDef) -> StubClass:  # L214-243
    """Build a StubClass from a class AST node."""
    ...

def extract_stub(source: str, rel_path: str) -> StubModule:  # L246-272
    """Parse Python source and extract all symbols with signatures and line ranges."""
    ...

def _render_param(p: StubParam) -> str:  # L275-281
    """Render a single parameter as a string for a function signature."""
    ...

def _render_function(func: StubFunction, indent: str) -> list[str]:  # L284-295
    """Render a function or method as stub lines, indented for methods."""
    ...

def _format_assignment_body(a: StubAssignment) -> str:  # L298-305
    """Render the 'name [: type] [= value]' portion of an assignment."""
    ...

def _render_assignment(a: StubAssignment, indent: str) -> str:  # L308-311
    """Render a module-level assignment as a stub line, with line range."""
    ...

def _render_class_attribute(a: StubAssignment, indent: str) -> str:  # L314-316
    """Render a class attribute as a stub line (no line range — class has one)."""
    ...

def render_stub(module: StubModule) -> str:  # L319-353
    """Render a StubModule as a .pyi file string."""
    ...

def _generate_stubs(source_root: Path) -> dict[Path, str]:  # L356-367
    """Return a mapping from stub relative paths to rendered stub content."""
    ...

def build_stubs(source_root: Path, output_dir: Path) -> None:  # L373-379
    """Write stub files for all symbols under source_root."""
    ...

class StubParam:  # L16-20
    """A function parameter with name and optional type annotation."""

    name: str
    annotation: str | None = None

class StubFunction:  # L24-33
    """A function or method with its signature and line range."""

    name: str
    params: list[StubParam] = field(default_factory=list)
    return_annotation: str | None = None
    docstring_excerpt: str | None = None
    start_line: int = 0
    end_line: int = 0
    is_async: bool = False

class StubAssignment:  # L37-50
    """A module-level or class-level assignment."""

    name: str
    annotation: str | None = None
    value_source: str | None = None
    start_line: int = 0
    end_line: int = 0
    is_type_alias: bool = False

class StubClass:  # L54-63
    """A class with its members and line range."""

    name: str
    bases: list[str] = field(default_factory=list)
    docstring_excerpt: str | None = None
    start_line: int = 0
    end_line: int = 0
    attributes: list[StubAssignment] = field(default_factory=list)
    methods: list[StubFunction] = field(default_factory=list)

class StubModule:  # L67-74
    """All symbols extracted from a single Python module."""

    rel_path: str
    imports: list[str] = field(default_factory=list)
    constants: list[StubAssignment] = field(default_factory=list)
    classes: list[StubClass] = field(default_factory=list)
    functions: list[StubFunction] = field(default_factory=list)
