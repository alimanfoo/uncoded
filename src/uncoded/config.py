"""Read uncoded configuration from pyproject.toml or .uncoded.toml."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

UNCODED_TOML = ".uncoded.toml"

# The roots that uncoded init names, in the order it names them.
_CONVENTIONAL_ROOTS = {
    "source-roots": ("src", "tests"),
    "doc-roots": ("README.md", "AGENTS.md", "docs"),
}


class ConfigError(Exception):
    """Raised when the project's configuration cannot be used."""


@dataclass(frozen=True)
class Config:
    """Uncoded configuration loaded from a project's config file."""

    project_root: Path
    source_roots: list[Path]
    doc_roots: list[Path]
    required_version: str | None


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
    """Return the ``[tool.uncoded]`` table of ``pyproject_path``, or None.

    Returns None when the file or the table is absent.
    """
    data = _load_toml(path=pyproject_path)
    return None if data is None else data.get("tool", {}).get("uncoded")


def _load_toml(*, path: Path) -> dict | None:
    """Parse the TOML file at ``path``, or return None when it is absent."""
    if not path.exists():
        return None
    with path.open("rb") as f:
        return tomllib.load(f)


def _config_file_at(*, directory: Path) -> tuple[Path, dict] | None:
    """Return the configuration file in ``directory`` and its settings, or None.

    A ``pyproject.toml`` without a ``[tool.uncoded]`` table is not a
    configuration file, so the search passes over it. Skips directories named
    ``.uncoded``. Raises :exc:`ConfigError` when ``pyproject.toml`` and
    ``.uncoded.toml`` both configure uncoded.
    """
    if directory.name == ".uncoded":
        return None
    pyproject = directory / "pyproject.toml"
    uncoded_toml = directory / UNCODED_TOML
    pyproject_settings = _pyproject_settings(pyproject_path=pyproject)
    uncoded_toml_settings = _load_toml(path=uncoded_toml)
    if uncoded_toml_settings is not None:
        if pyproject_settings is not None:
            raise ConfigError(
                "Ambiguous config: both pyproject.toml and .uncoded.toml "
                "configure uncoded in the same directory. "
                "Configure uncoded in one file only."
            )
        return uncoded_toml, uncoded_toml_settings
    if pyproject_settings is not None:
        return pyproject, pyproject_settings
    return None


def _find_config_file(*, start: Path) -> tuple[Path, dict] | None:
    """Return the nearest configuration file and its settings, from ``start`` up.

    The nearest directory with a result wins. Ambiguity is a same-directory
    condition only. Files at different levels do not conflict. Returns None
    when no configuration file is found.
    """
    start_resolved = start.resolve()
    for directory in [start_resolved, *start_resolved.parents]:
        result = _config_file_at(directory=directory)
        if result is not None:
            return result
    return None


def find_config(*, start: Path) -> Config | None:
    """Locate the configuration file and read all uncoded settings from it.

    Walks up from ``start`` looking for ``.uncoded.toml`` or a
    ``pyproject.toml`` with a ``[tool.uncoded]`` table. Returns None when no
    configuration file is found. Raises :exc:`ConfigError` when two files in
    the same directory both configure uncoded.
    """
    found = _find_config_file(start=start)
    if found is None:
        return None
    config_file, settings = found

    source_roots = [Path(r) for r in settings.get("source-roots", [])]
    doc_roots = [Path(r) for r in settings.get("doc-roots", [])]

    return Config(
        project_root=config_file.parent,
        source_roots=source_roots,
        doc_roots=doc_roots,
        required_version=settings.get("required-version"),
    )


def read_config(*, start: Path) -> Config:
    """Return the configuration that :func:`find_config` finds from ``start``.

    Raises :exc:`ConfigError` when no configuration file is found.
    """
    config = find_config(start=start)
    if config is None:
        raise ConfigError(
            "No configuration file found in this directory or above it. "
            "Run the command from inside the project, or configure uncoded "
            "in .uncoded.toml or in a [tool.uncoded] table in pyproject.toml."
        )
    return config


def render_conventional_config(*, directory: Path, required_version: str) -> str:
    """Return the text of a configuration file for the project in ``directory``.

    The file names as roots whichever of the conventional roots exist in
    ``directory``, and sets ``required_version``. Raises :exc:`ConfigError`
    when none of them exist.
    """
    roots = {
        setting: [name for name in names if (directory / name).exists()]
        for setting, names in _CONVENTIONAL_ROOTS.items()
    }
    if not any(roots.values()):
        looked_for = ", ".join(
            name for names in _CONVENTIONAL_ROOTS.values() for name in names
        )
        raise ConfigError(
            f"none of {looked_for} is in this directory, so there is nothing to "
            f"index and no configuration file was written. Write {UNCODED_TOML} "
            "by hand, with source-roots listing the directories of Python code "
            "and doc-roots listing the Markdown files and directories."
        )
    lines = [
        f"{setting} = {json.dumps(found)}" for setting, found in roots.items() if found
    ]
    lines.append(f"required-version = {json.dumps(required_version)}")
    return "\n".join(lines) + "\n"
