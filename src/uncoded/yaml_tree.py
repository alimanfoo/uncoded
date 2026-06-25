"""Shared YAML renderer for pure-key-hierarchy tree maps."""

import yaml


class _CleanDumper(yaml.SafeDumper):
    """YAML dumper that indents list items and suppresses 'null' values."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        """Force list items to be indented relative to their parent key."""
        return super().increase_indent(flow, False)


# Render None as empty rather than "null" so leaf entries appear as just "name:"
_CleanDumper.add_representer(
    type(None),
    lambda dumper, _: dumper.represent_scalar("tag:yaml.org,2002:null", ""),
)


def render_yaml_tree(header: str, mapping: dict) -> str:
    """Render a nested dict as a YAML string with a leading comment header."""
    body = yaml.dump(
        mapping,
        Dumper=_CleanDumper,
        default_flow_style=False,
        sort_keys=False,
    )
    return header + "\n" + body
