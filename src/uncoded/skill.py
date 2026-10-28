"""Generate skill files for the target repository."""

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml

from uncoded.markers import GENERATED_MARKER
from uncoded.sync import remove_file, sync_file

SKILL_ROOTS = [
    Path(".claude/skills"),  # Claude Code
    Path(".agents/skills"),  # Codex
]


@dataclass(frozen=True)
class Skill:
    """Frozen record of one skill: name, content file, and gate."""

    name: str
    description: str
    body_file: str
    gate: Literal["source", "docs"]
    is_navigation: bool = False


SKILLS: list[Skill] = [
    Skill(
        name="uncoded-consistency-review",
        description=(
            "Review a Python codebase for semantic and naming consistency. It"
            " reports only concrete disagreements between two claims about the"
            " same concept, with verbatim evidence for each claim. It assumes"
            " uncoded is installed (.uncoded/namespace.yaml and .uncoded/stubs/"
            " present)."
        ),
        body_file="consistency_review.md",
        gate="source",
    ),
    Skill(
        name="uncoded-code-navigation",
        description=(
            "Load once per session, before the first search, read, or edit of Python"
            " source in a codebase indexed by uncoded. Covers locating a symbol,"
            " reading a definition, or checking references before you refactor,"
            " rename, or delete."
        ),
        body_file="code_navigation.md",
        gate="source",
        is_navigation=True,
    ),
    Skill(
        name="uncoded-doc-navigation",
        description=(
            "Load once per session, before the first search or read of a codebase's"
            " Markdown documentation indexed by uncoded. Covers locating which file"
            " and section cover a topic, or orienting to what documentation exists."
        ),
        body_file="doc_navigation.md",
        gate="docs",
        is_navigation=True,
    ),
]


def _skill_path(*, root: Path, name: str) -> Path:
    """Return the SKILL.md path for a skill name under a given root."""
    return root / name / "SKILL.md"


def _is_built(*, skill: Skill, source: bool, docs: bool) -> bool:
    """Return whether the project's roots meet ``skill``'s gate."""
    return source if skill.gate == "source" else docs


def _render_content(*, skill: Skill) -> str:
    """Render the full SKILL.md content."""
    front = yaml.dump(
        {"name": skill.name, "description": skill.description},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )
    body = (files("uncoded") / skill.body_file).read_text(encoding="utf-8").lstrip("\n")
    return f"---\n{front}---\n\n<!-- {GENERATED_MARKER} -->\n\n{body}"


def _sync_one_skill(
    *,
    skill: Skill,
    source: bool,
    docs: bool,
    project_root: Path,
    check: bool,
) -> int:
    """Build one skill's files when its gate is met, or remove them otherwise.

    Returns the number of file changes (writes and removals).
    """
    changes = 0
    if _is_built(skill=skill, source=source, docs=docs):
        content = _render_content(skill=skill)
        for root in SKILL_ROOTS:
            changes += sync_file(
                path=_skill_path(root=root, name=skill.name),
                content=content,
                project_root=project_root,
                check=check,
            )
    else:
        for root in SKILL_ROOTS:
            changes += remove_file(
                path=_skill_path(root=root, name=skill.name),
                project_root=project_root,
                check=check,
            )
    return changes


def sync_skills(
    *,
    source: bool,
    docs: bool,
    project_root: Path,
    check: bool,
) -> int:
    """Sync all registered skill files for the target repository.

    For each skill, builds the skill files when its gate condition is met
    (gate "source" requires source=True; gate "docs" requires docs=True) and
    removes them otherwise.

    Returns the total number of file changes (writes and removals).
    """
    changes = 0
    for skill in SKILLS:
        changes += _sync_one_skill(
            skill=skill,
            source=source,
            docs=docs,
            project_root=project_root,
            check=check,
        )
    return changes


def agent_instructions(*, source: bool, docs: bool) -> str:
    """Return the lines for ``AGENTS.md`` or ``CLAUDE.md`` that load skills.

    Gives one line for each navigation skill that the project's roots build.
    """
    lines = [
        f"- Load the `{skill.name}` skill once per session, before searching,"
        f" reading or editing any {'code' if skill.gate == 'source' else 'docs'}."
        for skill in SKILLS
        if skill.is_navigation and _is_built(skill=skill, source=source, docs=docs)
    ]
    return "\n".join(["## Before you start", "", *lines]) + "\n"
