# src/uncoded/read_helpers.py

import sys
import tokenize
from pathlib import Path

def read_source_text(path: Path) -> str:
    ...

def read_source_text_or_warn(path: Path, *, warning_path: Path | str | None) -> str | None:
    ...

def _read_file_text_as_utf8(path: Path, *, display: Path | str | None) -> str | None:
    ...
