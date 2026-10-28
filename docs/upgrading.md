# Upgrading

To upgrade a project to a new release of uncoded:

1. Read [the changelog](changelog.md) for every release after the one that the
   project uses.
2. If the new release is major, follow the section below for each major release
   that the upgrade crosses, oldest first.
3. If a pre-commit hook runs uncoded, raise the version in its `entry` to the
   new release.
4. Run `uvx uncoded@<version> sync`, where `<version>` is the new release, and
   commit every file that the upgrade changes, including every installed skill
   file that the command writes, rewrites or removes.

## From version 4 to version 5

Version 5 no longer reads the `required-version` setting. Delete it from the
configuration file. The version in the `entry` of the pre-commit hook now pins
uncoded. If the project has no hook, add one as
[Refresh on commit](keeping-current.md#refresh-on-commit) says.

## From version 3 to version 4

Version 4 adds `uncoded init` and a required version, runs `body` and `refs`
only inside a project, and lays stubs out in the standard stub style.

1. Run version 4, which rewrites every stub in the new layout:

   ```sh
   uvx uncoded@4.0.0 sync
   ```

   Commit every installed skill file that it writes or rewrites.

2. Pin the project to version 4, so that every machine runs the same uncoded.
   Add this setting to the configuration file:

   ```toml
   required-version = "4.0.0"
   ```

   If a pre-commit hook runs uncoded, name the same version in its `entry`, as
   `uvx uncoded@4.0.0 sync`, since uncoded refuses any other version.

3. Delete any skill that an earlier version of uncoded wrote under a name it no
   longer uses, since version 4 no longer removes them:

   ```sh
   rm -rf .agents/skills/coherence-review .claude/skills/coherence-review
   rm -rf .agents/skills/uncoded-coherence-review .claude/skills/uncoded-coherence-review
   rm -rf .agents/skills/uncoded-review .claude/skills/uncoded-review
   ```

   Check first that none of them is a skill of the project's own.

4. Run `uncoded body` and `uncoded refs` from inside the project. They now stop
   outside a project, and when the `--in` file is outside the project directory.
   A script that ran them from elsewhere changes directory first.

5. On Windows, expect `/` between directories in the paths that `uncoded refs`
   prints. A script that read them with `\` changes to match.

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
   `uncoded-consistency-review`. Delete the old generated skill:

   ```sh
   rm -rf .agents/skills/uncoded-coherence-review .claude/skills/uncoded-coherence-review
   ```

4. Replace any always-on navigation instructions in `AGENTS.md` or `CLAUDE.md`
   with the skill-loading instructions from
   [Getting started](getting-started.md#tell-agents-to-use-the-skills).

## From version 1 to version 2

Version 2 replaces instruction injection with generated skills.

1. Run the final version 2 release to create the skill files:

   ```sh
   uvx uncoded@2.1.1 sync
   ```

   It also removes the version 1 skills, `coherence-review` and
   `uncoded-review`. Later releases leave them in place.

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
