# Changelog

This page lists every change to [the contract](compatibility.md), including
every fix that makes uncoded do what its documentation or its skills say.
Refactoring, tests, CI and the documentation get no entry. The release notes on
GitHub list every merged pull request.

Each release after 3.0.1 groups its entries under these headings, in this order,
and leaves out any heading that would be empty. Each heading names the type of
release that its entries make, as [Compatibility](compatibility.md#versions)
describes the types:

- **Breaking** for a change that makes the release major;
- **Added** for an addition that makes the release minor;
- **Changed** for any other change that makes the release minor; and
- **Fixed** for a fix that makes the release a patch.

A change stays under **Unreleased**, with the same headings, until a release
includes it. Each entry links the pull request that made the change.

## Unreleased

### Breaking

- On Windows, the paths that `uncoded refs` prints and the path comment in each
  stub use `/` to separate directories, as the namespace map and the docs map
  already do. So does every path in a message or a warning.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))

### Added

- `uncoded --version` prints the installed version.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))

### Fixed

- `uncoded refs` runs ty 0.0.92, in place of 0.0.53, and finds references that
  the older ty missed. ([#308](https://github.com/alimanfoo/uncoded/pull/308))
- `uncoded refs` on Windows prints each reference's path relative to the current
  directory, in place of a path that names no file.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))

## [3.0.1](https://github.com/alimanfoo/uncoded/releases/tag/v3.0.1) — 2026-10-09

- `uncoded refs` finds the project directory from a `.uncoded.toml`
  configuration file, as well as from a `pyproject.toml` one.
  ([#251](https://github.com/alimanfoo/uncoded/pull/251))
- `uncoded-code-navigation` tells the agent to start with the namespace map and
  to read a stub or source only when the task needs that detail, in place of
  reading the stub of every file it touches.
  ([#256](https://github.com/alimanfoo/uncoded/pull/256))

## [3.0.0](https://github.com/alimanfoo/uncoded/releases/tag/v3.0.0) — 2026-09-19

Before upgrading, follow
[Upgrading from version 2 to version 3](upgrading.md#from-version-2-to-version-3).

- `uncoded sync` writes `.uncoded/.gitignore`, which keeps the index out of Git.
  The navigation skills tell the agent to build a missing index, and to refresh
  it after editing indexed files.
  ([#241](https://github.com/alimanfoo/uncoded/pull/241))
- `uncoded-coherence-review` is renamed `uncoded-consistency-review`, and
  reports only disagreements between two claims about the same concept.
  `uncoded sync` removes the skill under its earlier names.
  ([#245](https://github.com/alimanfoo/uncoded/pull/245))
- The navigation skills tell the agent to load each of them once per session.
  ([#240](https://github.com/alimanfoo/uncoded/pull/240))

## [2.1.1](https://github.com/alimanfoo/uncoded/releases/tag/v2.1.1) — 2026-06-26

- A Markdown file that starts with a byte-order mark keeps its first heading in
  the docs map, and every stub carries the provenance marker.
  ([#201](https://github.com/alimanfoo/uncoded/pull/201))

## [2.1.0](https://github.com/alimanfoo/uncoded/releases/tag/v2.1.0) — 2026-06-24

- uncoded reads a Python file in the encoding that the file declares, and every
  installed skill file carries the provenance marker.
  ([#189](https://github.com/alimanfoo/uncoded/pull/189))
- The skills are reworded for clarity.
  ([#190](https://github.com/alimanfoo/uncoded/pull/190))

## [2.0.0](https://github.com/alimanfoo/uncoded/releases/tag/v2.0.0) — 2026-06-23

Before upgrading, follow
[Upgrading from version 1 to version 2](upgrading.md#from-version-1-to-version-2).

- uncoded generates its navigation guidance as the skills
  `uncoded-code-navigation` and `uncoded-doc-navigation`, and no longer writes a
  section into `AGENTS.md` or `CLAUDE.md`. The `instruction-files` configuration
  key is removed, and the `coherence-review` skill is renamed
  `uncoded-coherence-review`.
  ([#184](https://github.com/alimanfoo/uncoded/pull/184))
- `uncoded sync` skips a Markdown file that it cannot read, with a warning,
  instead of stopping. ([#177](https://github.com/alimanfoo/uncoded/pull/177))

## [1.2.0](https://github.com/alimanfoo/uncoded/releases/tag/v1.2.0) — 2026-06-19

- `uncoded sync` writes the coherence review skill only when source roots are
  configured, and leaves its section of `AGENTS.md` or `CLAUDE.md` alone after a
  Markdown formatter rewraps it.
  ([#172](https://github.com/alimanfoo/uncoded/pull/172))

## [1.1.0](https://github.com/alimanfoo/uncoded/releases/tag/v1.1.0) — 2026-06-18

- The `doc-roots` setting adds the docs map, and a `.uncoded.toml` file can hold
  the configuration in a project without a `pyproject.toml`.
  ([#165](https://github.com/alimanfoo/uncoded/pull/165))

## [1.0.1](https://github.com/alimanfoo/uncoded/releases/tag/v1.0.1) — 2026-05-19

- The guidance that uncoded writes into `AGENTS.md` or `CLAUDE.md`, and the
  coherence review skill, describe `uncoded refs` as finding references, not
  only callers. The skill runs uncoded through `uvx`.
  ([#160](https://github.com/alimanfoo/uncoded/pull/160))

## [1.0.0](https://github.com/alimanfoo/uncoded/releases/tag/v1.0.0) — 2026-05-18

- `uncoded body` prints a symbol's source, and `uncoded refs` finds its
  references with the ty language server. They replace Serena, and the
  `uncoded setup` command that configured it is removed.
  ([#132](https://github.com/alimanfoo/uncoded/pull/132),
  [#145](https://github.com/alimanfoo/uncoded/pull/145),
  [#151](https://github.com/alimanfoo/uncoded/pull/151))

## 0.x

Releases 0.1.0 to 0.7.1, from 2026-04-21 to 2026-05-14, came before uncoded's
first stable release. Their changes are in the
[GitHub releases](https://github.com/alimanfoo/uncoded/releases).
