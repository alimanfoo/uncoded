# src/uncoded/skill.py

from importlib.resources import files
from pathlib import Path
from uncoded.sync import remove_file, sync_file

SKILL_OUTPUTS = ...
LEGACY_SKILL_OUTPUTS = ...
_SKILL_CONTENT = (files('uncoded') / 'coherence_review.md').read_text(encoding='utf-8')

def sync_skill(*, project_root: Path, check: bool) -> bool:
    ...
