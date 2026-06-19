"""Generate skill files for the target repository."""

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Literal

import yaml

from uncoded.sync import remove_file, sync_file

SKILL_ROOTS = [
    Path(".claude/skills"),  # Claude Code
    Path(".agents/skills"),  # Codex
]


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body_file: str
    gate: Literal["code", "docs"]
    legacy_names: tuple[str, ...] = ()


SKILLS: list[Skill] = [
    Skill(
        name="uncoded-coherence-review",
        description=(
            "Perform a coherence review of a Python codebase: a diagnostic sweep for"
            " semantic drift, naming inconsistency, promissory mismatch, and structural"
            " incoherence. Produces a Markdown report of findings with verbatim"
            " evidence and confidence levels, for human investigation. Assumes uncoded"
            " is installed (.uncoded/namespace.yaml and .uncoded/stubs/ present)."
        ),
        body_file="coherence_review.md",
        gate="code",
        legacy_names=("coherence-review", "uncoded-review"),
    ),
    Skill(
        name="uncoded-code-navigation",
        description=(
            "Navigate Python source code in a codebase indexed by uncoded."
            " Load .uncoded/namespace.yaml first, read .pyi stubs before source"
            " files, and apply the dispatch rule: symbol name to uncoded body/refs,"
            " pattern or phrase to grep."
        ),
        body_file="code_navigation.md",
        gate="code",
    ),
    Skill(
        name="uncoded-doc-navigation",
        description=(
            "Navigate a codebase's Markdown documentation indexed by uncoded."
            " Load .uncoded/docs.yaml at session start to see every file and its"
            " heading hierarchy, then use Read or grep to reach a specific section."
        ),
        body_file="doc_navigation.md",
        gate="docs",
    ),
]


def _render_content(*, skill: Skill) -> str:
    """Render the full SKILL.md content: YAML frontmatter followed by the skill body."""
    front = yaml.dump(
        {"name": skill.name, "description": skill.description},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )
    body = (files("uncoded") / skill.body_file).read_text(encoding="utf-8").lstrip("\n")
    return f"---\n{front}---\n\n{body}"


def sync_skills(
    *,
    source: bool,
    docs: bool,
    project_root: Path,
    check: bool,
) -> int:
    """Sync all registered skill files for the target repository.

    For each skill, builds the skill files when its gate condition is met
    (gate "code" requires source=True; gate "docs" requires docs=True) and
    removes them otherwise. Always removes any legacy skill paths.

    Returns the total number of file changes (writes and removals).
    """
    changes = 0
    for skill in SKILLS:
        build = source if skill.gate == "code" else docs
        if build:
            content = _render_content(skill=skill)
            for root in SKILL_ROOTS:
                changes += sync_file(
                    root / skill.name / "SKILL.md",
                    content,
                    project_root=project_root,
                    check=check,
                )
        else:
            for root in SKILL_ROOTS:
                changes += remove_file(
                    root / skill.name / "SKILL.md",
                    project_root=project_root,
                    check=check,
                )
        for legacy_name in skill.legacy_names:
            for root in SKILL_ROOTS:
                changes += remove_file(
                    root / legacy_name / "SKILL.md",
                    project_root=project_root,
                    check=check,
                )
    return changes
