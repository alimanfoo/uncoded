"""Read uncoded configuration from pyproject.toml or .uncoded.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Raised by read_config when the configuration cannot be determined."""


@dataclass(frozen=True)
class Config:
    """Uncoded configuration loaded from a project's config file."""

    project_root: Path
    source_roots: list[Path]
    doc_roots: list[Path]


def find_pyproject_toml(start: Path) -> Path | None:
    """Walk up from ``start`` looking for ``pyproject.toml``."""
    current = start.resolve()
    while True:
        candidate = current / "pyproject.toml"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _has_uncoded_section(*, pyproject_path: Path) -> bool:
    """Return True if ``pyproject_path`` contains a ``[tool.uncoded]`` section."""
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    try:
        data["tool"]["uncoded"]
        return True
    except KeyError:
        return False


def _config_file_at(*, directory: Path) -> Path | None:
    """Return the config file in ``directory``, or None.

    Skips directories named ``.uncoded``. Per-directory resolution rules:

    - ``pyproject.toml`` with ``[tool.uncoded]`` AND ``.uncoded.toml`` both
      present → raises :exc:`ConfigError` (configure uncoded in one file only).
    - Only ``pyproject.toml`` with ``[tool.uncoded]`` → home is the pyproject.
    - Only ``.uncoded.toml`` → home is the ``.uncoded.toml``.
    - ``pyproject.toml`` without ``[tool.uncoded]``, no ``.uncoded.toml``
      → home is the pyproject (bare Python project; roots default to empty).
    - ``pyproject.toml`` without ``[tool.uncoded]`` AND ``.uncoded.toml``
      → home is the ``.uncoded.toml`` (bare pyproject does not shadow it).
    - Neither file → returns None.
    """
    if directory.name == ".uncoded":
        return None
    pyproject = directory / "pyproject.toml"
    uncoded_toml = directory / ".uncoded.toml"
    has_uncoded_toml = uncoded_toml.exists()
    if pyproject.exists():
        has_section = _has_uncoded_section(pyproject_path=pyproject)
        if has_section and has_uncoded_toml:
            raise ConfigError(
                "Ambiguous config: both pyproject.toml and .uncoded.toml "
                "configure uncoded in the same directory. "
                "Configure uncoded in one file only."
            )
        if not has_section and has_uncoded_toml:
            # Bare pyproject does not shadow a sibling .uncoded.toml.
            return uncoded_toml
        return pyproject
    if has_uncoded_toml:
        return uncoded_toml
    return None


def _find_config_file(*, start: Path) -> Path | None:
    """Return the nearest config file walking up from ``start``.

    The nearest directory with a result wins. Ambiguity is a same-directory
    condition only. Files at different levels do not conflict. Returns None
    when no config file is found.
    """
    start_resolved = start.resolve()
    for directory in [start_resolved, *start_resolved.parents]:
        result = _config_file_at(directory=directory)
        if result is not None:
            return result
    return None


def read_config(start: Path) -> Config:
    """Locate the config file and read all uncoded settings from it.

    Walks up from ``start`` looking for ``pyproject.toml`` or
    ``.uncoded.toml``. Raises :exc:`ConfigError` when no config file is
    found, or when two config files in the same directory both configure
    uncoded. A found config file with no uncoded settings returns a Config
    with empty root lists.
    """
    config_file = _find_config_file(start=start)
    if config_file is None:
        raise ConfigError(
            "No pyproject.toml or .uncoded.toml found. Create one to configure uncoded."
        )

    with config_file.open("rb") as f:
        data = tomllib.load(f)

    if config_file.name == "pyproject.toml":
        try:
            section = data["tool"]["uncoded"]
        except KeyError:
            section = {}
    else:
        # .uncoded.toml uses top-level keys with no wrapper section.
        section = data

    source_roots = [Path(r) for r in section.get("source-roots", [])]
    doc_roots = [Path(r) for r in section.get("doc-roots", [])]

    return Config(
        project_root=config_file.parent,
        source_roots=source_roots,
        doc_roots=doc_roots,
    )
