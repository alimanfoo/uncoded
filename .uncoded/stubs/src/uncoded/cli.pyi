# src/uncoded/cli.py

import argparse
import sys
from pathlib import Path
from uncoded.body import resolve_body
from uncoded.config import ConfigError, read_config
from uncoded.docs_map import build_docs_map, iter_doc_files, render_docs_map
from uncoded.extract import extract_modules, iter_source_files
from uncoded.instruction_files import SECTION_CODE, SECTION_DOCS, sync_instruction_file
from uncoded.namespace_map import build_map, render_map
from uncoded.refs import find_refs
from uncoded.resolver import NamePath, SymbolNotFound, UnsupportedNamePath
from uncoded.skill import sync_skill
from uncoded.stubs import build_stubs, remove_all_stubs
from uncoded.sync import remove_file, sync_file

def _sync_code_artefacts(*, build: bool, configured_source_roots: list[Path], project_root: Path, resolved_project_root: Path, check: bool) -> int | None:
    ...

def _sync(*, start: Path | None, check: bool) -> int:
    ...

def _body(*, name_path: str, in_path: str) -> int:
    ...

def _refs(*, name_path: str, in_path: str) -> int:
    ...

def main() -> int:
    ...
