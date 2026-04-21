# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'  # L28
MCP_SERVER_SERENA = ...  # L30-45
SERENA_PROJECT_YML = ...  # L47-61
SERENA_ALLOWED_TOOLS = ...  # L63-81
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}  # L83-87

def read_project_name() -> str:  # L90-100
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:  # L103-120
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:  # L123-134
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:  # L137-167
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:  # L170-191
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
