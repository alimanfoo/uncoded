# Upgrading

From version 2, follow the steps below. From version 1, complete
[the version 1 to 2 steps](#from-version-1-to-version-2) first.

## From version 2 to version 3

Version 3 keeps generated indexes local, renames the semantic consistency
review, and makes navigation skills load once per session.

1. Stop tracking `.uncoded/`, then rebuild the index locally:

   ```sh
   git rm -r --cached .uncoded
   uvx uncoded sync
   ```

   Commit the updated files under `.agents/skills/` and `.claude/skills/`. The
   generated `.uncoded/.gitignore` keeps the rebuilt index out of Git.

2. Add `always_run: true` to the local `uncoded` pre-commit hook. The ignored
   index must also be refreshed when a commit only deletes files.

3. Change every skill pointer from `uncoded-coherence-review` to
   `uncoded-consistency-review`. Running `uncoded sync` removes the old
   generated skill.

4. Replace any always-on navigation instructions in `AGENTS.md` or `CLAUDE.md`
   with the skill-loading instructions from
   [Getting started](getting-started.md#tell-agents-to-use-the-skills).

## From version 1 to version 2

Version 2 replaces instruction injection with generated skills.

1. Run the final version 2 release to create the skill files:

   ```sh
   uvx uncoded@2.1.1 sync
   ```

2. Remove the old marker blocks from `AGENTS.md` or `CLAUDE.md`:

   ```text
   <!-- uncoded:start ... -->
   ...
   <!-- uncoded:end -->
   ```

   ```text
   <!-- uncoded:docs:start ... -->
   ...
   <!-- uncoded:docs:end -->
   ```

3. Change every skill pointer from `coherence-review` to
   `uncoded-coherence-review`.

4. Remove `instruction-files` from `pyproject.toml` or `.uncoded.toml` because
   version 2 no longer reads it.

5. To keep navigation always on, add the skill-loading instructions from
   [Getting started](getting-started.md#tell-agents-to-use-the-skills) to
   `AGENTS.md` or `CLAUDE.md`.
