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
    """Frozen record of one skill: name, content file, gate, and any legacy names."""

    name: str
    description: str
    body_file: str
    gate: Literal["code", "docs"]
    legacy_names: tuple[str, ...] = ()


SKILLS: list[Skill] = [
    Skill(
        name="uncoded-coherence-review",
        description=(
            "Review a Python codebase for coherence. It sweeps for semantic"
            " drift, naming inconsistency, mismatch between a symbol's name,"
            " signature, and docstring, and structural incoherence. It produces a"
            " Markdown report of"
            " findings, with verbatim"
            " evidence and confidence levels, for human investigation. It assumes"
            " uncoded is installed (.uncoded/namespace.yaml and .uncoded/stubs/"
            " present)."
        ),
        body_file="coherence_review.md",
        gate="code",
        legacy_names=("coherence-review", "uncoded-review"),
    ),
    Skill(
        name="uncoded-code-navigation",
        description=(
            "Use before searching, reading, or editing Python source in a codebase"
            " indexed by uncoded. This covers locating a symbol, reading a definition,"
            " or checking references before you refactor, rename, or delete."
        ),
        body_file="code_navigation.md",
        gate="code",
    ),
    Skill(
        name="uncoded-doc-navigation",
        description=(
            "Use before searching or reading a codebase's Markdown documentation"
            " indexed by uncoded. This covers locating which file and section cover a"
            " topic, or orienting to what documentation exists."
        ),
        body_file="doc_navigation.md",
        gate="docs",
    ),
]


def _skill_path(root: Path, name: str) -> Path:
    """Return the SKILL.md path for a skill name under a given root."""
    return root / name / "SKILL.md"


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
    return f"---\n{front}---\n\n<!-- {GENERATED_MARKER} -->\n\n{body}"


def _remove_skill_file(*, path: Path, project_root: Path, check: bool) -> bool:
    """Remove a skill's SKILL.md and prune its parent directory if now empty.

    Returns True if the file was (or would be) removed. In apply mode, removes
    the parent directory when it becomes empty after the removal; that cleanup
    is not counted as a separate change.
    """
    removed = remove_file(path, project_root=project_root, check=check)
    if removed and not check:
        parent = project_root / path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
    return removed


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
                    _skill_path(root, skill.name),
                    content,
                    project_root=project_root,
                    check=check,
                )
        else:
            for root in SKILL_ROOTS:
                changes += _remove_skill_file(
                    path=_skill_path(root, skill.name),
                    project_root=project_root,
                    check=check,
                )
        for legacy_name in skill.legacy_names:
            for root in SKILL_ROOTS:
                changes += _remove_skill_file(
                    path=_skill_path(root, legacy_name),
                    project_root=project_root,
                    check=check,
                )
    return changes
