# src/uncoded/claude_md.py

from pathlib import Path

def generate_section() -> str:  # L46-48
    """Return the full delimited uncoded section for insertion into CLAUDE.md."""
    ...

def _replace_or_append(existing: str, section: str) -> str:  # L51-61
    """Replace the delimited section in existing text, or append it if absent."""
    ...

def sync_claude_md(path: Path) -> None:  # L64-75
    """Write or update the uncoded navigation section in CLAUDE.md."""
    ...
