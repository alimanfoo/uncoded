# src/uncoded/refs.py

from __future__ import annotations
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast
from urllib.parse import urlparse
from uncoded.config import find_pyproject_toml

TY_VERSION = '0.0.37'

def query_references(in_path: Path, position: tuple[int, int]) -> list[Reference]:
    ...

def _find_root(in_path: Path) -> Path:
    ...

def _terminate(*, proc: subprocess.Popen[bytes]) -> None:
    ...

def _run_exchange(*, stdin: IO[bytes], stdout: IO[bytes], in_path: Path, position: tuple[int, int], root: Path) -> list[Reference]:
    ...

def _write_message(*, stream: IO[bytes], msg: dict) -> None:
    ...

def _read_message(*, stream: IO[bytes]) -> dict:
    ...

def _read_response(*, stream: IO[bytes], request_id: int) -> dict:
    ...

def _uri_to_path(uri: str) -> Path:
    ...

class Reference:
    path: Path
    line: int
    character: int
