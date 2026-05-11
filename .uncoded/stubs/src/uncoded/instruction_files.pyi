# src/uncoded/instruction_files.py

from pathlib import Path
from uncoded.sync import sync_file

MARKER_START = '<!-- uncoded:start -->'
MARKER_END = '<!-- uncoded:end -->'
DEFAULT_INSTRUCTION_FILES = [Path('CLAUDE.md'), Path('AGENTS.md')]
_SECTION_BODY = ...
SECTION = f'{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n'

def _replace_or_append(existing: str, section: str) -> str:
    ...

def sync_instruction_file(path: Path, *, project_root: Path, check: bool) -> bool:
    ...
