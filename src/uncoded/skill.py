"""Generate the coherence-review skill file for the target repository."""

from importlib.resources import files
from pathlib import Path

from uncoded.sync import remove_file, sync_file

SKILL_OUTPUTS = [
    Path(".claude/skills/coherence-review/SKILL.md"),  # Claude Code
    Path(".agents/skills/coherence-review/SKILL.md"),  # Codex
]

LEGACY_SKILL_OUTPUTS = [
    Path(".claude/skills/uncoded-review/SKILL.md"),  # Claude Code
    Path(".agents/skills/uncoded-review/SKILL.md"),  # Codex
]

_SKILL_CONTENT = (files("uncoded") / "coherence_review.md").read_text(encoding="utf-8")


def sync_skill(*, project_root: Path, check: bool, build: bool) -> bool:
    """Sync the coherence-review skill file to all supported agent locations.

    When build is True, write the skill files under project_root.
    When build is False, remove any existing skill files. In both cases,
    remove legacy skill files left by older versions of uncoded.
    """
    results: list[bool] = []
    if build:
        results.extend(
            sync_file(path, _SKILL_CONTENT, project_root=project_root, check=check)
            for path in SKILL_OUTPUTS
        )
    else:
        results.extend(
            remove_file(path, project_root=project_root, check=check)
            for path in SKILL_OUTPUTS
        )
    results.extend(
        remove_file(path, project_root=project_root, check=check)
        for path in LEGACY_SKILL_OUTPUTS
    )
    return any(results)
