# src/uncoded/cli.py

import argparse
import sys
from pathlib import Path
from uncoded.extract import walk_source
from uncoded.namespace_map import build_map, render_map
from uncoded.stubs import DEFAULT_STUBS_OUTPUT, build_stubs, generate_stubs

def main(argv: list[str] | None):  # L14-38
    ...

def cmd_sync(args: argparse.Namespace) -> int:  # L52-65
    ...

def cmd_check(args: argparse.Namespace) -> int:  # L68-98
    ...
