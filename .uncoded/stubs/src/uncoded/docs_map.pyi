# src/uncoded/docs_map.py

from collections.abc import Iterable, Iterator
from pathlib import Path
from uncoded.markers import GENERATED_MARKER
from uncoded.read_helpers import read_doc_text_or_warn
from uncoded.yaml_tree import render_yaml_tree

DOCS_HEADER = ...

def extract_headings(text: str) -> list[tuple[int, str]]:
    ...

def _unique_key(*, parent: dict, title: str) -> str:
    ...

def _collapse_empty(*, mapping: dict) -> dict | None:
    ...

def iter_doc_files(doc_root: Path, project_root: Path) -> Iterator[tuple[str, Path]]:
    ...

def build_docs_map(files: Iterable[tuple[str, Path]]) -> dict:
    ...

def render_docs_map(mapping: dict) -> str:
    ...
