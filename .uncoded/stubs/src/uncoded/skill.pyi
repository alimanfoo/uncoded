# src/uncoded/skill.py

from pathlib import Path
from uncoded.sync import remove_file, sync_file

SKILL_OUTPUTS = ...  # L7-10
LEGACY_SKILL_OUTPUTS = ...  # L12-15
_SKILL_CONTENT = ...  # L17-381

def sync_skill(*, check: bool) -> bool:  # L384-388
    """Write the coherence-review skill file to all supported agent locations."""
    ...
