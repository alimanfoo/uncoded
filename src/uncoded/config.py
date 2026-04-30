"""Read uncoded configuration from pyproject.toml."""

import tomllib
from pathlib import Path

from uncoded.instruction_files import DEFAULT_INSTRUCTION_FILES


def find_pyproject_toml() -> Path | None:
    """Search for pyproject.toml starting from cwd, walking up."""
    current = Path.cwd()
    while True:
        candidate = current / "pyproject.toml"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def read_project_name() -> str:
    """Read the project name from pyproject.toml, falling back to the cwd name."""
    toml_path = find_pyproject_toml()
    if toml_path is None:
        return Path.cwd().name
    with toml_path.open("rb") as f:
        data = tomllib.load(f)
    try:
        return data["project"]["name"]
    except KeyError:
        return Path.cwd().name


def read_source_roots() -> list[Path]:
    """Read source roots from [tool.uncoded] source-roots in pyproject.toml."""
    toml_path = find_pyproject_toml()
    if toml_path is None:
        raise FileNotFoundError(
            "No pyproject.toml found. Add [tool.uncoded] source-roots to configure."
        )

    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        roots = data["tool"]["uncoded"]["source-roots"]
    except KeyError:
        raise KeyError(
            "No [tool.uncoded] source-roots found in pyproject.toml."
        ) from None

    return [Path(r) for r in roots]


def read_instruction_files() -> list[Path]:
    """Read instruction files from [tool.uncoded] instruction-files in pyproject.toml.

    Falls back to ``DEFAULT_INSTRUCTION_FILES`` if the key is absent or no
    ``pyproject.toml`` is found, so that ``uncoded`` works on a fresh repo
    without explicit configuration.
    """
    toml_path = find_pyproject_toml()
    if toml_path is None:
        return list(DEFAULT_INSTRUCTION_FILES)

    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        files = data["tool"]["uncoded"]["instruction-files"]
    except KeyError:
        return list(DEFAULT_INSTRUCTION_FILES)

    return [Path(f) for f in files]
