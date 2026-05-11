# src/uncoded/sync.py

from pathlib import Path

def sync_file(path: Path, content: str, *, project_root: Path, check: bool) -> bool:
    ...

def remove_file(path: Path, *, project_root: Path, check: bool) -> bool:
    ...
