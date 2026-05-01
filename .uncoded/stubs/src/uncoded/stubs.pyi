# src/uncoded/stubs.py

"""Generate .pyi stub files for agent navigation."""

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from uncoded.extract import _property_kind, iter_source_files
from uncoded.sync import remove_file, sync_file

VALUE_WIDTH_CAP = 80
DEFAULT_STUBS_OUTPUT = Path('.uncoded/stubs')

def _first_sentence(node: ast.AsyncFunctionDef | ast.FunctionDef | ast.ClassDef | ast.Module) -> str | None:
    """Return the first sentence of a node's docstring, or None."""
    ...

def _extract_params(args: ast.arguments) -> list[StubParam]:
    """Extract parameters from a function argument node, without defaults."""
    ...

def _render_value(value: ast.expr) -> str:
    """Render an expression as source, eliding to '...' if too long or multi-line."""
    ...

def _extract_assignment(node: ast.Assign | ast.AnnAssign | ast.TypeAlias) -> StubAssignment | None:
    """Build a StubAssignment from an assignment-style AST node."""
    ...

def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> StubFunction:
    """Build a StubFunction from a function or method AST node."""
    ...

def _property_attribute(node: ast.FunctionDef | ast.AsyncFunctionDef) -> StubAssignment:
    """Build a StubAssignment representing a @property as a class attribute."""
    ...

def _extract_class(node: ast.ClassDef) -> StubClass:
    """Build a StubClass from a class AST node."""
    ...

def extract_stub(source: str, rel_path: str) -> StubModule:
    """Parse Python source and extract imports, constants, classes, and functions."""
    ...

def _render_param(p: StubParam) -> str:
    """Render a single parameter as a string for a function signature."""
    ...

def _render_function(func: StubFunction, indent: str) -> list[str]:
    """Render a function or method as stub lines, indented for methods."""
    ...

def _format_assignment_body(a: StubAssignment) -> str:
    """Render the 'name [: type] [= value]' portion of an assignment."""
    ...

def _render_assignment(a: StubAssignment, indent: str) -> str:
    """Render a module-level assignment as a stub line."""
    ...

def render_stub(module: StubModule) -> str:
    """Render a StubModule as a .pyi file string."""
    ...

def _generate_stubs(files: Iterable[tuple[str, str]]) -> dict[Path, str]:
    """Return a mapping from stub relative paths to rendered stub content."""
    ...

def _write_stubs(stubs: dict[Path, str], source_root: Path, output_dir: Path, base: Path, *, check: bool) -> int:
    """Write *stubs* under *output_dir* and prune orphans under *source_root*."""
    ...

def build_stubs(source_root: Path, output_dir: Path, base: Path | None, *, check: bool) -> int:
    """Sync stub files for all symbols under source_root, removing any orphans."""
    ...

class StubParam:
    """A function parameter with name and optional type annotation."""

    name: str
    annotation: str | None = None

class StubFunction:
    """A function or method with its signature."""

    name: str
    params: list[StubParam] = field(default_factory=list)
    return_annotation: str | None = None
    docstring_excerpt: str | None = None
    is_async: bool = False

class StubAssignment:
    """A module-level or class-level assignment."""

    name: str
    annotation: str | None = None
    value_source: str | None = None
    is_type_alias: bool = False

class StubClass:
    """A class with its members."""

    name: str
    bases: list[str] = field(default_factory=list)
    docstring_excerpt: str | None = None
    attributes: list[StubAssignment] = field(default_factory=list)
    methods: list[StubFunction] = field(default_factory=list)

class StubModule:
    """All symbols extracted from a single Python module."""

    rel_path: str
    docstring_excerpt: str | None = None
    imports: list[str] = field(default_factory=list)
    constants: list[StubAssignment] = field(default_factory=list)
    classes: list[StubClass] = field(default_factory=list)
    functions: list[StubFunction] = field(default_factory=list)
