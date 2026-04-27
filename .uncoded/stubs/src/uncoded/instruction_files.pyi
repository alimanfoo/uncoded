# src/uncoded/instruction_files.py

from pathlib import Path
from uncoded.sync import sync_file

MARKER_START = '<!-- uncoded:start -->'
MARKER_END = '<!-- uncoded:end -->'
DEFAULT_INSTRUCTION_FILES = [Path('CLAUDE.md'), Path('AGENTS.md')]
_SECTION_BODY = ...
SECTION = f'{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n'

def generate_section() -> str:
    """Return the full delimited uncoded section for an instruction file."""
    ...

def _replace_or_append(existing: str, section: str) -> str:
    """Replace the delimited section in existing text, or append it if absent."""
    ...

def sync_instruction_file(path: Path, *, check: bool) -> bool:
    """Write or update the uncoded navigation section in an instruction file."""
    ...
