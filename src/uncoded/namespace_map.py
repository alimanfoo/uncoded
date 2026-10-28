"""Generate a YAML namespace map from extracted symbols."""

from pathlib import Path

from uncoded.extract import (
    AssignmentSymbol,
    ClassSymbol,
    FunctionSymbol,
    PythonFile,
    Symbol,
    TypeAliasSymbol,
)
from uncoded.markers import GENERATED_MARKER
from uncoded.yaml_tree import render_yaml_tree

HEADER = f"""\
# Namespace map of this codebase, for agent navigation.
# {GENERATED_MARKER}
#
# Pure key hierarchy (no lists, no values); indent to zoom in.
# Directory keys end with "/".
#
# For signatures and types, see stubs:
#   src/foo/bar.py  →  .uncoded/stubs/src/foo/bar.pyi
"""


# The kinds of symbol in the order that the map lists them under a file.
_KIND_ORDER = (AssignmentSymbol | TypeAliasSymbol, ClassSymbol, FunctionSymbol)


def _members(*, symbol: Symbol) -> dict | None:
    """Return the map entry under ``symbol``: a class's members, or None.

    A class with no members maps to None, as every other symbol does. A name
    defined more than once in the class body is listed once.
    """
    if not isinstance(symbol, ClassSymbol):
        return None
    members = [s.name for s in symbol.attributes] + [s.name for s in symbol.methods]
    return dict.fromkeys(members) or None


def build_map(*, python_files: list[PythonFile]) -> dict:
    """Build a nested dict representing the namespace.

    Keys are paths relative to the project directory. Directory keys have a
    trailing slash. Symbols sit directly under their file key, assignments
    first, then classes, then functions. A name defined more than once in the
    module body is listed once, where it is first defined, as the kind of its
    later definition.
    """
    root: dict = {}

    for python_file in python_files:
        parts = Path(python_file.rel_path).parts
        node = root

        # Create intermediate directory entries
        for dir_part in parts[:-1]:
            key = dir_part + "/"
            if key not in node:
                node[key] = {}
            node = node[key]

        symbols = {symbol.name: symbol for symbol in python_file.symbols}.values()
        node[parts[-1]] = {
            symbol.name: _members(symbol=symbol)
            for kind in _KIND_ORDER
            for symbol in symbols
            if isinstance(symbol, kind)
        }

    return root


def render_map(*, namespace: dict) -> str:
    """Render a namespace map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(header=HEADER, mapping=namespace)
