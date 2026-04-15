"""Generate a YAML namespace map from extracted symbols."""

from pathlib import Path

import yaml

from uncoded.extract import ModuleInfo


class _CleanDumper(yaml.SafeDumper):
    """YAML dumper that indents list items and suppresses 'null' values."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


# Render None as empty rather than "null" so leaf symbols appear as just "name:"
_CleanDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)


def build_map(modules: list[ModuleInfo]) -> dict:
    """Build a nested dict representing the namespace.

    Keys are repo-relative paths. Directory keys have a trailing slash.
    Symbols sit directly under their file key.
    """
    root: dict = {}

    for module in modules:
        parts = Path(module.rel_path).parts
        current = root

        # Create intermediate directory entries
        for dir_part in parts[:-1]:
            key = dir_part + "/"
            if key not in current:
                current[key] = {}
            current = current[key]

        # Build the file entry — symbols directly under the file key.
        # Classes with methods map to their method list.
        # Classes without methods and bare functions map to None.
        file_entry: dict = {}

        for cls in module.classes:
            members = cls.attributes + cls.methods
            file_entry[cls.name] = {m: None for m in members} if members else None

        for func in module.functions:
            file_entry[func] = None

        current[parts[-1]] = file_entry

    return root


def render_map(namespace: dict) -> str:
    """Render a namespace map dict as a YAML string."""
    return yaml.dump(
        namespace,
        Dumper=_CleanDumper,
        default_flow_style=False,
        sort_keys=False,
    )
