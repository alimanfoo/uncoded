# src/uncoded/serena_setup.py

import json
from pathlib import Path
from typing import Literal
import yaml
from uncoded.config import read_project_name

type _Status = Literal['wrote', 'updated', 'unchanged']
SERENA_VERSION = '1.1.2'
MCP_SERVER_SERENA = ...
SERENA_PROJECT_YML = ...
SERENA_ALLOWED_TOOLS = ...
_STATUS_VERB: dict[_Status, str] = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}

def _sync_mcp_json(path: Path) -> _Status:
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _write_serena_project_if_absent(path: Path, project_name: str) -> _Status:
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> _Status:
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup(root: Path | None) -> int:
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
