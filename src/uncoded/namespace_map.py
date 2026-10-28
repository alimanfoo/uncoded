"""Generate a YAML namespace map from extracted symbols."""

from uncoded.extract import ClassSymbol, PythonFile
from uncoded.markers import GENERATED_MARKER
from uncoded.yaml_tree import nest_by_path, render_yaml_tree

_HEADER = f"""\
# Namespace map of this codebase, for agent navigation.
# {GENERATED_MARKER}
#
# Pure key hierarchy (no lists, no values); indent to zoom in.
# Directory keys end with "/".
#
# For signatures and types, see stubs:
#   src/foo/bar.py  →  .uncoded/stubs/src/foo/bar.pyi
"""


def _members(*, cls: ClassSymbol) -> dict | None:
    """Return the map entry under ``cls``: its members, or None when it has none.

    A name defined more than once in the class body is listed once.
    """
    members = [s.name for s in cls.attributes] + [s.name for s in cls.methods]
    return dict.fromkeys(members) or None


def _file_entry(*, python_file: PythonFile) -> dict:
    """Return the map entry of ``python_file``: its symbols, by kind.

    Lists assignments first, then classes, then functions. A name defined more
    than once in the module body is listed once, where it is first defined, as
    the kind of its later definition.
    """
    later = {symbol.name: symbol for symbol in python_file.symbols}
    symbols = PythonFile(rel_path=python_file.rel_path, symbols=list(later.values()))
    return {
        **dict.fromkeys(s.name for s in symbols.assignments),
        **{cls.name: _members(cls=cls) for cls in symbols.classes},
        **dict.fromkeys(s.name for s in symbols.functions),
    }


def build_map(*, python_files: list[PythonFile]) -> dict:
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


def render_map(*, namespace: dict) -> str:
    """Render a namespace map dict as a YAML string with an explanatory header."""
    return render_yaml_tree(header=_HEADER, mapping=namespace)
