# src/uncoded/serena_setup.py

import json
import tomllib
from pathlib import Path
from uncoded.config import find_pyproject_toml

SERENA_VERSION = '1.1.2'  # L30
MCP_SERVER_SERENA = ...  # L32-47
SERENA_PROJECT_YML = ...  # L49-63
SERENA_ALLOWED_TOOLS = ...  # L65-83
_STATUS_VERB = {'wrote': 'Wrote', 'updated': 'Updated', 'unchanged': 'Unchanged'}  # L85-89

def read_project_name() -> str:  # L92-102
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    ...

def _sync_mcp_json(path: Path) -> str:  # L105-122
    """Write or merge Serena into ``.mcp.json``."""
    ...

def _sync_serena_project(path: Path, project_name: str) -> str:  # L125-136
    """Write ``.serena/project.yml`` if absent."""
    ...

def _sync_claude_settings(path: Path) -> str:  # L139-169
    """Write or merge Serena allowlist into ``.claude/settings.json``."""
    ...

def setup_serena(root: Path | None) -> int:  # L172-193
    """Generate Serena + ty + Claude Code configuration under ``root``."""
    ...
