# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'  # L33
MCP_SERVER_SERENA = ...  # L35-50
SERENA_PROJECT_YML = ...  # L52-59
SERENA_ALLOWED_TOOLS = ...  # L61-79
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}  # L81-85

def read_project_name() -> str:  # L88-98
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:  # L101-125
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:  # L128-139
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:  # L142-172
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:  # L175-197
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
