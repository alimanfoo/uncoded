# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'
MCP_SERVER_SERENA = ...
SERENA_PROJECT_YML = ...
SERENA_ALLOWED_TOOLS = ...
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}

def read_project_name() -> str:
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
