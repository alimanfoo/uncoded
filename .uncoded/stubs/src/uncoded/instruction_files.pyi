# src/uncoded/instruction_files.py

from importlib.resources import files
from pathlib import Path
from uncoded.sync import sync_file

MARKER_START = '<!-- uncoded:start -->'
MARKER_END = '<!-- uncoded:end -->'
MARKER_DOCS_START = '<!-- uncoded:docs:start -->'
MARKER_DOCS_END = '<!-- uncoded:docs:end -->'
DEFAULT_INSTRUCTION_FILES = [Path('CLAUDE.md'), Path('AGENTS.md')]
_CODE_SECTION_BODY = (files('uncoded') / 'dispatch_rule.md').read_text(encoding='utf-8').rstrip('\n')
SECTION_CODE = f'{MARKER_START}\n{_CODE_SECTION_BODY}\n{MARKER_END}\n'
_DOCS_SECTION_BODY = (files('uncoded') / 'docs_rule.md').read_text(encoding='utf-8').rstrip('\n')
SECTION_DOCS = f'{MARKER_DOCS_START}\n{_DOCS_SECTION_BODY}\n{MARKER_DOCS_END}\n'

def _apply_section(text: str, start: str, end: str, body: str | None) -> str:
    ...

def sync_instruction_file(path: Path, *, code_section: str | None, docs_section: str | None, project_root: Path, check: bool) -> bool:
    ...
