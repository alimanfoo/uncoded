"""Generate configuration files for Serena + ty LSP integration.

Writes three files that wire a repo up to Serena's MCP bridge with ty as
the Python language-server backend, in the shape Claude Code picks up
automatically:

* ``.mcp.json`` — registers the Serena MCP server so Claude Code launches
  it via ``uvx`` on session start, with the web dashboard disabled.
* ``.serena/project.yml`` — selects ty over Serena's default backend
  (pyright), keeps Serena out of uncoded's generated stubs, and narrows
  Serena's surface to pure LSP operations: memory, onboarding,
  dashboard, and shell-exec tools are all excluded. uncoded's namespace
  map and stubs already give agents a project-wide view, so Serena's
  memory-based project understanding is redundant and noisy alongside
  it.
* ``.claude/settings.json`` — enables the Serena server and allowlists
  the nine tools (``initial_instructions`` plus the eight LSP tools —
  symbol lookup, reference search, and the edit family) so they run
  without a prompt.

JSON files merge into existing content: pre-existing non-Serena MCP
servers and permissions are preserved, while the Serena entry itself
refreshes to the current ``SERENA_VERSION`` so re-running after a bump
propagates the pin. The YAML project file is only written when absent,
to avoid clobbering hand-edited Serena config.
"""

import json
from pathlib import Path
from typing import Literal

import yaml

from uncoded.config import read_project_name

# Closed set of one-word statuses returned by the three sync helpers and
# rendered through ``_STATUS_VERB`` by ``setup()``. Typed as a literal
# union so a typo in a helper's return value is a ty error rather than a
# runtime ``KeyError`` when ``setup()`` formats the per-file line.
type _Status = Literal["wrote", "updated", "unchanged"]

# Pin the Serena version so every repo that runs `uncoded setup` gets
# the same, tested integration. On bump, re-run `uncoded setup` to
# refresh the pin in existing repos — the sync overwrites the serena
# entry in .mcp.json with the current MCP_SERVER_SERENA value. A
# dogfooding test in tests/test_serena_setup.py guards against drift.
SERENA_VERSION = "1.1.2"

MCP_SERVER_SERENA = {
    "command": "uvx",
    "args": [
        "--from",
        f"serena-agent=={SERENA_VERSION}",
        "serena",
        "start-mcp-server",
        "--context",
        "claude-code",
        "--transport",
        "stdio",
        "--project-from-cwd",
        "--open-web-dashboard",
        "false",
    ],
}

# Static fields of ``.serena/project.yml``. ``project_name`` is injected
# per call by ``_write_serena_project_if_absent`` and serialised via
# ``yaml.safe_dump`` so YAML-special characters in the name (colons,
# quotes, leading dashes, braces, etc.) are escaped instead of producing
# malformed YAML or a parse exception. Field order is preserved by
# ``sort_keys=False`` at dump time; ``project_name`` is placed first by
# constructing the dict with it as the first key.
SERENA_PROJECT_YML = {
    "languages": ["python_ty"],
    "ignored_paths": [".uncoded"],
    "excluded_tools": [
        "execute_shell_command",
        "list_memories",
        "read_memory",
        "write_memory",
        "edit_memory",
        "delete_memory",
        "rename_memory",
        "onboarding",
        "check_onboarding_performed",
        "open_dashboard",
    ],
}

SERENA_ALLOWED_TOOLS = [
    "mcp__serena__initial_instructions",
    "mcp__serena__find_symbol",
    "mcp__serena__find_referencing_symbols",
    "mcp__serena__get_symbols_overview",
    "mcp__serena__rename_symbol",
    "mcp__serena__safe_delete_symbol",
    "mcp__serena__insert_before_symbol",
    "mcp__serena__insert_after_symbol",
    "mcp__serena__replace_symbol_body",
]

_STATUS_VERB: dict[_Status, str] = {
    "wrote": "Wrote",
    "updated": "Updated",
    "unchanged": "Unchanged",
}


def _sync_mcp_json(path: Path) -> _Status:
    """Write or merge Serena into ``.mcp.json``.

    Non-Serena MCP servers already in the file are preserved. The
    ``serena`` entry itself is always refreshed to ``MCP_SERVER_SERENA``
    so a ``SERENA_VERSION`` bump flows into existing repos on the next
    ``uncoded setup`` run. Anyone who has hand-customised the ``serena``
    entry should keep their edits out of this file (add a sibling entry
    instead, or re-apply after refresh).

    Returns a one-word status: ``wrote``, ``updated``, or ``unchanged``.
    """
    if path.exists():
        data = json.loads(path.read_text())
        servers = data.setdefault("mcpServers", {})
        if servers.get("serena") == MCP_SERVER_SERENA:
            return "unchanged"
        servers["serena"] = MCP_SERVER_SERENA
        status = "updated"
    else:
        data = {"mcpServers": {"serena": MCP_SERVER_SERENA}}
        status = "wrote"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return status


def _write_serena_project_if_absent(path: Path, project_name: str) -> _Status:
    """Write ``.serena/project.yml`` if absent.

    Returns ``wrote`` or ``unchanged``. An existing file is never touched:
    YAML merging preserves neither comments nor key order, and a user who
    has customised their Serena config should keep it.
    """
    if path.exists():
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"project_name": project_name, **SERENA_PROJECT_YML}
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return "wrote"


def _sync_claude_settings(path: Path) -> _Status:
    """Write or merge Serena allowlist into ``.claude/settings.json``.

    Returns ``wrote``, ``updated``, or ``unchanged``.
    """
    if path.exists():
        data = json.loads(path.read_text())
        status = "unchanged"
    else:
        data = {}
        status = "wrote"

    enabled = data.setdefault("enabledMcpjsonServers", [])
    if "serena" not in enabled:
        enabled.append("serena")
        if status == "unchanged":
            status = "updated"

    permissions = data.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])
    for tool in SERENA_ALLOWED_TOOLS:
        if tool not in allow:
            allow.append(tool)
            if status == "unchanged":
                status = "updated"

    if status == "unchanged":
        return status
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return status


# `root` is an injection seam for tests; the CLI always uses `Path.cwd()`.
def setup(root: Path | None = None) -> int:
    """Generate Serena + ty + Claude Code configuration under ``root``.

    JSON files merge into existing content, refreshing the Serena
    entries so a re-run picks up a bumped ``SERENA_VERSION``. The
    Serena YAML project file is only written when absent.
    """
    if root is None:
        root = Path.cwd()
    project_name = read_project_name()

    mcp_path = root / ".mcp.json"
    serena_path = root / ".serena" / "project.yml"
    claude_path = root / ".claude" / "settings.json"

    results = [
        (mcp_path, _sync_mcp_json(mcp_path)),
        (serena_path, _write_serena_project_if_absent(serena_path, project_name)),
        (claude_path, _sync_claude_settings(claude_path)),
    ]
    for path, status in results:
        print(f"{_STATUS_VERB[status]} {path.relative_to(root)}")
    return 0
