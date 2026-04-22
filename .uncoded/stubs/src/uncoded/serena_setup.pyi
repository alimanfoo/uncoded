# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'  # L31
MCP_SERVER_SERENA = ...  # L33-48
SERENA_PROJECT_YML = ...  # L50-64
SERENA_ALLOWED_TOOLS = ...  # L66-84
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}  # L86-90

def read_project_name() -> str:  # L93-103
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:  # L106-123
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:  # L126-137
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:  # L140-170
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:  # L173-194
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
