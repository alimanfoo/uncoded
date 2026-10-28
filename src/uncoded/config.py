"""Read uncoded configuration from pyproject.toml or .uncoded.toml."""

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from uncoded.read_helpers import failure_reason

UNCODED_TOML = ".uncoded.toml"

# One exact version, written as uncoded writes its own, since the required
# version is compared with uncoded's own as a string: three release numbers and
# any pre-release, post-release, development or local part, as in "3.1.0",
# "3.1.0rc1" or "3.1.0.dev2+g1a2b3c4".
_EXACT_VERSION = re.compile(
    r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?(?:\.post\d+)?(?:\.dev\d+)?"
    r"(?:\+[a-z0-9]+(?:\.[a-z0-9]+)*)?"
)

# The roots that uncoded init names, by kind, in the order it names them.
_CONVENTIONAL_ROOTS: dict[Literal["source", "doc"], tuple[str, ...]] = {
    "source": ("src", "tests"),
    "doc": ("README.md", "AGENTS.md", "docs"),
}


class ConfigError(Exception):
    """Raised when the project's configuration cannot be used."""


@dataclass(frozen=True)
class Config:
    """Uncoded configuration loaded from a project's configuration file."""

    config_file: Path
    source_roots: list[Path]
    doc_roots: list[Path]
    required_version: str | None

    @property
    def project_root(self) -> Path:
        """The project directory, the directory of the configuration file."""
        return self.config_file.parent


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
        raise _config_file_error(path=pyproject_path, problem="tool is not a table")
    settings = tool.get("uncoded")
    if settings is not None and not isinstance(settings, dict):
        raise _config_file_error(
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
        raise _config_file_error(path=path, problem=failure_reason(error=e)) from e
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise _config_file_error(path=path, problem=f"not valid TOML: {e}") from e


def _config_file_error(*, path: Path, problem: str) -> ConfigError:
    """Return the error for the configuration file at ``path`` and its problem."""
    return ConfigError(f"{path.as_posix()}: {problem}")


def _config_file_at(*, directory: Path) -> tuple[Path, dict] | None:
    """Return the configuration file in ``directory`` and its settings, or None.

    A ``pyproject.toml`` without a ``[tool.uncoded]`` table is not a
    configuration file, so the search passes over it. Skips directories named
    ``.uncoded``. Raises :exc:`ConfigError` when ``pyproject.toml`` and
    ``.uncoded.toml`` both configure uncoded, or when either cannot be used.
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
                f"both {pyproject.as_posix()} and {uncoded_toml.as_posix()} "
                "configure uncoded. Configure uncoded in one file only."
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
    the same directory both configure uncoded, or when a file that the search
    reads cannot be used.
    """
    found = _find_config_file(start=start)
    if found is None:
        return None
    config_file, settings = found
    return Config(
        config_file=config_file,
        source_roots=_roots(
            settings=settings, setting="source-roots", config_file=config_file
        ),
        doc_roots=_roots(
            settings=settings, setting="doc-roots", config_file=config_file
        ),
        required_version=_required_version(settings=settings, config_file=config_file),
    )


def _roots(*, settings: dict, setting: str, config_file: Path) -> list[Path]:
    """Return the roots that ``setting`` lists, or no roots when it is unset.

    Raises :exc:`ConfigError`, naming ``config_file``, when the setting is not
    a list of strings.
    """
    roots = settings.get(setting, [])
    if not isinstance(roots, list) or not all(isinstance(r, str) for r in roots):
        raise _config_file_error(
            path=config_file, problem=f"{setting} is not a list of strings"
        )
    return [Path(r) for r in roots]


def _required_version(*, settings: dict, config_file: Path) -> str | None:
    """Return the ``required-version`` setting, or None when it is unset.

    Raises :exc:`ConfigError`, naming ``config_file``, when the setting is not
    one exact version.
    """
    version = settings.get("required-version")
    if version is None or (
        isinstance(version, str) and _EXACT_VERSION.fullmatch(version)
    ):
        return version
    raise _config_file_error(
        path=config_file,
        problem='required-version is not one exact version, such as "3.1.0"',
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


def is_inside_project(*, path: Path, project_root: Path) -> bool:
    """Return whether ``path`` is inside ``project_root``.

    Symbolic links are resolved first, so a link inside ``project_root`` that
    leads out of it is outside.
    """
    return path.resolve().is_relative_to(project_root.resolve())


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
    if not is_inside_project(path=resolved, project_root=project_root):
        raise ConfigError(
            f"{root_label} is outside the project directory. "
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
