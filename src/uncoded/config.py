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


def find_pyproject_toml(*, start: Path) -> Path | None:
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


def _pyproject_settings(*, pyproject_path: Path) -> dict | None:
    """Return the ``[tool.uncoded]`` table of ``pyproject_path``, or None."""
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("uncoded")


def _uncoded_toml_settings(*, uncoded_toml_path: Path) -> dict:
    """Return the settings of ``uncoded_toml_path``, held as top-level keys."""
    with uncoded_toml_path.open("rb") as f:
        return tomllib.load(f)


def _config_file_at(*, directory: Path) -> tuple[Path, dict] | None:
    """Return the config file in ``directory`` and its settings, or None.

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
        settings = _pyproject_settings(pyproject_path=pyproject)
        has_section = settings is not None
        if has_section and has_uncoded_toml:
            raise ConfigError(
                "Ambiguous config: both pyproject.toml and .uncoded.toml "
                "configure uncoded in the same directory. "
                "Configure uncoded in one file only."
            )
        if not has_section and has_uncoded_toml:
            # Bare pyproject does not shadow a sibling .uncoded.toml.
            return uncoded_toml, _uncoded_toml_settings(uncoded_toml_path=uncoded_toml)
        return pyproject, settings or {}
    if has_uncoded_toml:
        return uncoded_toml, _uncoded_toml_settings(uncoded_toml_path=uncoded_toml)
    return None


def _find_config_file(*, start: Path) -> tuple[Path, dict] | None:
    """Return the nearest config file and its settings, walking up from ``start``.

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


def read_config(*, start: Path) -> Config:
    """Locate the config file and read all uncoded settings from it.

    Walks up from ``start`` looking for ``pyproject.toml`` or
    ``.uncoded.toml``. Raises :exc:`ConfigError` when no config file is
    found, or when two config files in the same directory both configure
    uncoded. A found config file with no uncoded settings returns a Config
    with empty root lists.
    """
    found = _find_config_file(start=start)
    if found is None:
        raise ConfigError(
            "No pyproject.toml or .uncoded.toml found. Create one to configure uncoded."
        )
    config_file, settings = found

    source_roots = [Path(r) for r in settings.get("source-roots", [])]
    doc_roots = [Path(r) for r in settings.get("doc-roots", [])]

    return Config(
        project_root=config_file.parent,
        source_roots=source_roots,
        doc_roots=doc_roots,
    )
