"""Shared nesting and YAML rendering for pure-key-hierarchy tree maps."""

from collections.abc import Iterable

import yaml


class _CleanDumper(yaml.SafeDumper):
    """YAML dumper that suppresses 'null' values."""


# Render None as empty rather than "null" so leaf entries appear as just "name:"
_CleanDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)


def render_yaml_tree(*, header: str, mapping: dict) -> str:
    """Render a nested dict as a YAML string with a leading comment header."""
    body = yaml.dump(
        mapping,
        Dumper=_CleanDumper,
        default_flow_style=False,
        sort_keys=False,
    )
    return header + "\n" + body


def nest_by_path(*, entries: Iterable[tuple[str, dict | None]]) -> dict:
    """Nest each file's entry under keys for the directories that hold it.

    ``entries`` pairs each file's path relative to the project directory, with
    ``/`` separators, with its entry. Directory keys end with "/".
    """
    root: dict = {}
    for rel_path, entry in entries:
        *directories, file_name = rel_path.split("/")
        node = root
        for directory in directories:
            node = node.setdefault(f"{directory}/", {})
        node[file_name] = entry
    return root
