# src/uncoded/skill.py

from pathlib import Path
from uncoded.sync import sync_file

SKILL_OUTPUT = Path('.claude/skills/uncoded-review/SKILL.md')  # L7
_SKILL_CONTENT = ...  # L9-344

def sync_skill(*, check: bool) -> bool:  # L347-349
    """Write the uncoded-review skill file if it differs from what's on disk."""
    ...
