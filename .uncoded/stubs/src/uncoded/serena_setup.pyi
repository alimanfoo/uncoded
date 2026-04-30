# src/uncoded/serena_setup.py

import json
from pathlib import Path
from uncoded.config import read_project_name

SERENA_VERSION = '1.1.2'
MCP_SERVER_SERENA = ...
SERENA_PROJECT_YML = ...
SERENA_ALLOWED_TOOLS = ...
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}

def _sync_mcp_json(path: Path) -> str:
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup(root: Path | None) -> int:
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
