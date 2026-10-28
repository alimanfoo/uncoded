"""Generate the installed skill files for a project."""

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml

from uncoded.markers import GENERATED_MARKER
from uncoded.sync import remove_file, sync_file

SKILL_DIRECTORIES = [
    Path(".claude/skills"),  # Claude Code
    Path(".agents/skills"),  # Codex
]


@dataclass(frozen=True)
class _Skill:
    """Frozen record of one skill: name, skill source, and gate."""

    name: str
    description: str
    skill_source: str
    gate: Literal["source", "doc"]
    is_navigation: bool = False


_SKILLS: list[_Skill] = [
    _Skill(
        name="uncoded-consistency-review",
        description=(
            "Review a Python codebase for semantic and naming consistency. It"
            " reports only concrete disagreements between two claims about the"
            " same concept, with verbatim evidence for each claim. It assumes"
            " uncoded is installed (.uncoded/namespace.yaml and .uncoded/stubs/"
            " present)."
        ),
        skill_source="consistency_review.md",
        gate="source",
    ),
    _Skill(
        name="uncoded-code-navigation",
        description=(
            "Load once per session, before the first search, read, or edit of Python"
            " source in a codebase indexed by uncoded. Covers locating a symbol,"
            " reading a definition, or checking references before you refactor,"
            " rename, or delete."
        ),
        skill_source="code_navigation.md",
        gate="source",
        is_navigation=True,
    ),
    _Skill(
        name="uncoded-doc-navigation",
        description=(
            "Load once per session, before the first search or read of a codebase's"
            " Markdown documentation indexed by uncoded. Covers locating which file"
            " and section cover a topic, or orienting to what documentation exists."
        ),
        skill_source="doc_navigation.md",
        gate="doc",
        is_navigation=True,
    ),
]


def _skill_path(*, skill_directory: Path, name: str) -> Path:
    """Return the SKILL.md path for a skill name in a given skill directory."""
    return skill_directory / name / "SKILL.md"


def _is_built(*, skill: _Skill, source: bool, doc: bool) -> bool:
    """Return whether the project's roots meet ``skill``'s gate."""
    return source if skill.gate == "source" else doc


def _render_content(*, skill: _Skill) -> str:
    """Render the full SKILL.md content."""
    front = yaml.dump(
        {"name": skill.name, "description": skill.description},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )
    text = files("uncoded").joinpath(skill.skill_source).read_text(encoding="utf-8")
    body = text.lstrip("\n")
    return f"---\n{front}---\n\n<!-- {GENERATED_MARKER} -->\n\n{body}"


def _sync_one_skill(
    *,
    skill: _Skill,
    source: bool,
    doc: bool,
    project_directory: Path,
    check: bool,
) -> int:
    """Build one skill's files when its gate is met, or remove them otherwise.

    Returns the number of file changes (writes and removals).
    """
    changes = 0
    if _is_built(skill=skill, source=source, doc=doc):
        content = _render_content(skill=skill)
        for skill_directory in SKILL_DIRECTORIES:
            changes += sync_file(
                path=_skill_path(skill_directory=skill_directory, name=skill.name),
                content=content,
                project_directory=project_directory,
                check=check,
            )
    else:
        for skill_directory in SKILL_DIRECTORIES:
            changes += remove_file(
                path=_skill_path(skill_directory=skill_directory, name=skill.name),
                project_directory=project_directory,
                check=check,
            )
    return changes


def sync_skills(
    *,
    source: bool,
    doc: bool,
    project_directory: Path,
    check: bool,
) -> int:
    """Sync all registered skill files for the project.

    For each skill, builds the skill files when its gate condition is met
    (gate "source" requires source=True; gate "doc" requires doc=True) and
    removes them otherwise.

    Returns the total number of file changes (writes and removals).
    """
    changes = 0
    for skill in _SKILLS:
        changes += _sync_one_skill(
            skill=skill,
            source=source,
            doc=doc,
            project_directory=project_directory,
            check=check,
        )
    return changes


def agent_instructions(*, source: bool, doc: bool) -> str:
    """Return the lines for ``AGENTS.md`` or ``CLAUDE.md`` that load skills.

    Gives one line for each navigation skill that the project's roots build.
    """
    lines = [
        f"- Load the `{skill.name}` skill once per session, before searching,"
        f" reading or editing any {'code' if skill.gate == 'source' else 'docs'}."
        for skill in _SKILLS
        if skill.is_navigation and _is_built(skill=skill, source=source, doc=doc)
    ]
    return "\n".join(["## Before you start", "", *lines]) + "\n"
