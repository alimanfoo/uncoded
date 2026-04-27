# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'  # L38
MCP_SERVER_SERENA = ...  # L40-55
SERENA_PROJECT_YML = ...  # L57-73
SERENA_ALLOWED_TOOLS = ...  # L75-85
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}  # L87-91

def read_project_name() -> str:  # L94-104
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:  # L107-131
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:  # L134-145
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:  # L148-178
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:  # L181-203
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
