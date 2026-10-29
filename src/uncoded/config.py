"""Read uncoded configuration from pyproject.toml."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from uncoded.read_helpers import failure_reason

# The roots that uncoded init names, by kind, in the order it names them.
_CONVENTIONAL_ROOTS: dict[Literal["source", "doc"], tuple[str, ...]] = {
    "source": ("src", "tests"),
    "doc": ("README.md", "AGENTS.md", "docs"),
}


class ConfigError(Exception):
    """Raised when the project's configuration cannot be used."""


@dataclass(frozen=True)
class Config:
    """The uncoded settings loaded from a project's configuration file."""

    configuration_file: Path
    source_roots: list[Path]
    doc_roots: list[Path]

    @property
    def project_directory(self) -> Path:
        """The project directory, the directory of the configuration file."""
        return self.configuration_file.parent


def _pyproject_settings(*, pyproject_path: Path) -> dict | None:
    """Return the ``[tool.uncoded]`` table of ``pyproject_path``, or None.

    Returns None when the file or the table is absent. Raises
    :exc:`ConfigError`, naming the file, when ``tool`` or ``tool.uncoded`` is
    not a table.
    """
    data = _load_toml(path=pyproject_path)
    if data is None:
        return None
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        raise _configuration_file_error(
            path=pyproject_path, problem="tool is not a table"
        )
    settings = tool.get("uncoded")
    if settings is not None and not isinstance(settings, dict):
        raise _configuration_file_error(
            path=pyproject_path, problem="tool.uncoded is not a table"
        )
    return settings


def _load_toml(*, path: Path) -> dict | None:
    """Parse the TOML file at ``path``, or return None when it is absent.

    Raises :exc:`ConfigError`, naming the file, when the file cannot be read or
    is not valid TOML.
    """
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return None
    except OSError as e:
        raise _configuration_file_error(
            path=path, problem=failure_reason(error=e)
        ) from e
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise _configuration_file_error(
            path=path, problem=f"not valid TOML: {e}"
        ) from e


def _configuration_file_error(*, path: Path, problem: str) -> ConfigError:
    """Return the error for the configuration file at ``path`` and its problem."""
    return ConfigError(f"{path.as_posix()}: {problem}")


def _configuration_file_at(*, directory: Path) -> tuple[Path, dict] | None:
    """Return the configuration file in ``directory`` and its settings, or None.

    A ``pyproject.toml`` without a ``[tool.uncoded]`` table is not a
    configuration file, so the search passes over it. Raises
    :exc:`ConfigError` when the file cannot be used.
    """
    pyproject = directory / "pyproject.toml"
    pyproject_settings = _pyproject_settings(pyproject_path=pyproject)
    if pyproject_settings is not None:
        return pyproject, pyproject_settings
    return None


def _find_configuration_file(*, start: Path) -> tuple[Path, dict] | None:
    """Return the nearest configuration file and its settings, from ``start`` up.

    Returns None when no configuration file is found.
    """
    start_resolved = start.resolve()
    for directory in [start_resolved, *start_resolved.parents]:
        result = _configuration_file_at(directory=directory)
        if result is not None:
            return result
    return None


def find_config(*, start: Path) -> Config | None:
    """Locate the configuration file and read all uncoded settings from it.

    Walks up from ``start`` looking for a ``pyproject.toml`` with a
    ``[tool.uncoded]`` table. Returns None when no configuration file is found.
    Raises :exc:`ConfigError` when a file that the search reads cannot be used.
    """
    found = _find_configuration_file(start=start)
    if found is None:
        return None
    configuration_file, settings = found
    return Config(
        configuration_file=configuration_file,
        source_roots=_roots(
            settings=settings,
            setting="source-roots",
            configuration_file=configuration_file,
        ),
        doc_roots=_roots(
            settings=settings,
            setting="doc-roots",
            configuration_file=configuration_file,
        ),
    )


def _roots(*, settings: dict, setting: str, configuration_file: Path) -> list[Path]:
    """Return the roots that ``setting`` lists, or no roots when it is unset.

    Raises :exc:`ConfigError`, naming ``configuration_file``, when the setting is not
    a list of strings.
    """
    roots = settings.get(setting, [])
    if not isinstance(roots, list) or not all(isinstance(r, str) for r in roots):
        raise _configuration_file_error(
            path=configuration_file, problem=f"{setting} is not a list of strings"
        )
    return [Path(r) for r in roots]


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


def is_inside_project(*, path: Path, project_directory: Path) -> bool:
    """Return whether ``path`` is inside ``project_directory``.

    Symbolic links are resolved first, so a link inside ``project_directory`` that
    leads out of it is outside.
    """
    return path.resolve().is_relative_to(project_directory.resolve())


def validate_root(
    *, configured: Path, kind: Literal["source", "doc"], config: Config
) -> Path:
    """Resolve the configured root against the project directory and return it.

    Raises :exc:`ConfigError`, naming the configuration file and the ``kind``
    of root, when the root is outside the project directory, does not exist,
    or is not a directory or, for a doc root, a Markdown file.
    """
    resolved, problem = _resolve_root(
        configured=configured, kind=kind, project_directory=config.project_directory
    )
    if problem is not None:
        raise _configuration_file_error(
            path=config.configuration_file,
            problem=f"{kind}-roots names {configured.as_posix()}, which {problem}",
        )
    return resolved


def _resolve_root(
    *, configured: Path, kind: Literal["source", "doc"], project_directory: Path
) -> tuple[Path, str | None]:
    """Return the configured root resolved against ``project_directory``.

    Pairs it with what stops the root being used, or None when nothing does.
    """
    resolved = (project_directory / configured).resolve()
    if not is_inside_project(path=resolved, project_directory=project_directory):
        return resolved, "is outside the project directory"
    if not resolved.exists():
        return resolved, "does not exist"
    if resolved.is_dir():
        return resolved, None
    if kind == "source":
        return resolved, "is not a directory"
    if resolved.is_file() and resolved.suffix == ".md":
        return resolved, None
    return resolved, "is not a directory or a Markdown file"


def render_conventional_config(*, directory: Path) -> str:
    """Return a conventional ``[tool.uncoded]`` table for ``directory``.

    The table names as roots whichever of the conventional roots in
    ``directory`` are valid roots. Raises :exc:`ConfigError` when none of them
    are.
    """
    roots: dict[str, list[str]] = {kind: [] for kind in _CONVENTIONAL_ROOTS}
    for kind, names in _CONVENTIONAL_ROOTS.items():
        for name in names:
            _resolved, problem = _resolve_root(
                configured=Path(name), kind=kind, project_directory=directory
            )
            if problem is None:
                roots[kind].append(name)
    if not any(roots.values()):
        raise ConfigError(
            "found none of the source roots "
            f"{', '.join(_CONVENTIONAL_ROOTS['source'])} or the doc roots "
            f"{', '.join(_CONVENTIONAL_ROOTS['doc'])} in this directory, so "
            "changed no configuration file. Add [tool.uncoded] to pyproject.toml "
            "by hand, with source-roots listing the directories of Python code "
            "and doc-roots listing the Markdown files and directories."
        )
    lines = ["[tool.uncoded]"]
    lines.extend(
        f"{kind}-roots = {json.dumps(found)}" for kind, found in roots.items() if found
    )
    return "\n".join(lines) + "\n"
