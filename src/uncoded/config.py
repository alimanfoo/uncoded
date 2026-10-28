"""Read uncoded configuration from pyproject.toml or .uncoded.toml."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

UNCODED_TOML = ".uncoded.toml"

# The roots that uncoded init names, by kind, in the order it names them.
_CONVENTIONAL_ROOTS: dict[Literal["source", "doc"], tuple[str, ...]] = {
    "source": ("src", "tests"),
    "doc": ("README.md", "AGENTS.md", "docs"),
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
            "Run the command from inside the project, or set uncoded up with "
            "uncoded init."
        )
    return config


def validate_root(
    *, configured: Path, kind: Literal["source", "doc"], project_root: Path
) -> Path:
    """Resolve the configured root against ``project_root`` and return it.

    Raises :exc:`ConfigError` when the root resolves outside ``project_root``,
    or is not a directory or, for a doc root, a Markdown file. ``kind`` also
    selects the noun used in the error messages.
    """
    root_label = f"{kind} root {configured.as_posix()}"
    resolved = (project_root / configured).resolve()
    if not resolved.is_relative_to(project_root.resolve()):
        raise ConfigError(
            f"{root_label} is outside the project root. "
            f"Check {kind}-roots in your uncoded config file."
        )
    accepts_md_file = kind == "doc"
    is_valid = resolved.is_dir() or (
        accepts_md_file and resolved.is_file() and resolved.suffix == ".md"
    )
    if not is_valid:
        if accepts_md_file:
            raise ConfigError(
                f"{root_label} is not a directory or .md file. "
                f"Check {kind}-roots in your uncoded config file."
            )
        raise ConfigError(
            f"{root_label} is not a directory. "
            f"Check {kind}-roots in your uncoded config file."
        )
    return resolved


def _is_valid_root(
    *, configured: Path, kind: Literal["source", "doc"], project_root: Path
) -> bool:
    """Return whether :func:`validate_root` accepts the configured root."""
    try:
        validate_root(configured=configured, kind=kind, project_root=project_root)
    except ConfigError:
        return False
    return True


def render_conventional_config(*, directory: Path, required_version: str) -> str:
    """Return the text of a configuration file for the project in ``directory``.

    The file names as roots whichever of the conventional roots in
    ``directory`` are valid roots, and sets ``required_version``. Raises
    :exc:`ConfigError` when none of them are.
    """
    roots = {
        kind: [
            name
            for name in names
            if _is_valid_root(configured=Path(name), kind=kind, project_root=directory)
        ]
        for kind, names in _CONVENTIONAL_ROOTS.items()
    }
    if not any(roots.values()):
        raise ConfigError(
            "found none of the source roots "
            f"{', '.join(_CONVENTIONAL_ROOTS['source'])} or the doc roots "
            f"{', '.join(_CONVENTIONAL_ROOTS['doc'])} in this directory, so "
            f"wrote no configuration file. Write {UNCODED_TOML} by hand, with "
            "source-roots listing the directories of Python code and doc-roots "
            "listing the Markdown files and directories."
        )
    lines = [
        f"{kind}-roots = {json.dumps(found)}" for kind, found in roots.items() if found
    ]
    lines.append(f"required-version = {json.dumps(required_version)}")
    return "\n".join(lines) + "\n"
