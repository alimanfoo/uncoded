"""Generate a YAML namespace map from extracted symbols."""

from uncoded.extract import ClassSymbol, PythonFile, Symbol
from uncoded.markers import GENERATED_MARKER
from uncoded.yaml_tree import nest_by_path, render_yaml_tree

_NAMESPACE_HEADER = f"""\
# Namespace map of this codebase, for agent navigation.
# {GENERATED_MARKER}
#
# Pure key hierarchy (no lists, no values); indent to zoom in.
# Directory keys end with "/".
#
# For signatures and types, see stubs:
#   src/foo/bar.py  →  .uncoded/stubs/src/foo/bar.pyi
"""


def _members(*, symbol: Symbol) -> dict | None:
    """Return the map entry under ``symbol``: a class's members, else None.

    A name defined more than once in the class body is listed once, where it is
    first defined.
    """
    if not isinstance(symbol, ClassSymbol):
        return None
    return {member.name: None for member in symbol.members} or None


def _file_entry(*, python_file: PythonFile) -> dict:
    """Return the map entry of ``python_file``: its symbols, in file order.

    A name defined more than once in the module body is listed once, where it is
    first defined.
    """
    return {s.name: _members(symbol=s) for s in python_file.symbols}


def build_namespace_map(*, python_files: list[PythonFile]) -> dict:
    """Build a nested dict representing the namespace.

    Keys are paths relative to the project directory. Directory keys have a
    trailing slash. Symbols sit directly under their file key.
    """
    return nest_by_path(
        entries=(
            (python_file.rel_path, _file_entry(python_file=python_file))
            for python_file in python_files
        )
    )


def render_namespace_map(*, mapping: dict) -> str:
    """Render a namespace map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(header=_NAMESPACE_HEADER, mapping=mapping)
