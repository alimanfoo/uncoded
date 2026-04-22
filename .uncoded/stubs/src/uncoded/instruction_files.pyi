# src/uncoded/instruction_files.py

from pathlib import Path
from uncoded.sync import sync_file

MARKER_START = '<!-- uncoded:start -->'  # L14
MARKER_END = '<!-- uncoded:end -->'  # L15
DEFAULT_INSTRUCTION_FILES = [Path('CLAUDE.md'), Path('AGENTS.md')]  # L17
_SECTION_BODY = ...  # L19-99
SECTION = f'{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n'  # L101

def generate_section() -> str:  # L104-106
    """Return the full delimited uncoded section for an instruction file."""
    ...

def _replace_or_append(existing: str, section: str) -> str:  # L109-119
    """Replace the delimited section in existing text, or append it if absent."""
    ...

def sync_instruction_file(path: Path, *, check: bool) -> bool:  # L122-133
    """Write or update the uncoded navigation section in an instruction file."""
    ...
