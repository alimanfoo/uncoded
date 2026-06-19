# src/uncoded/skill.py

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal
import yaml
from uncoded.sync import remove_file, sync_file

SKILL_ROOTS = [Path('.claude/skills'), Path('.agents/skills')]
SKILLS: list[Skill] = ...

def _render_content(*, skill: Skill) -> str:
    ...

def sync_skills(*, source: bool, docs: bool, project_root: Path, check: bool) -> int:
    ...

class Skill:
    name: str
    description: str
    body_file: str
    gate: Literal['code', 'docs']
    legacy_names: tuple[str, ...] = ()
