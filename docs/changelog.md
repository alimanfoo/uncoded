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

## [5.0.0](https://github.com/alimanfoo/uncoded/releases/tag/v5.0.0) — 2026-10-29

Before upgrading, follow
[Upgrading from version 4 to version 5](upgrading.md#from-version-4-to-version-5).

### Breaking

- uncoded no longer reads the `required-version` setting, and `uncoded init` no
  longer writes it. uncoded runs at any version, and a project pins its version
  in the `entry` of its pre-commit hook.
  ([#380](https://github.com/alimanfoo/uncoded/pull/380))

### Changed

- The navigation and consistency review skills tell the agent to run
  `uvx uncoded sync` and `uvx uncoded body`, in place of the project's
  configured command, which nothing configures.
  ([#407](https://github.com/alimanfoo/uncoded/pull/407))
- The docs map lists every CommonMark ATX heading, including one indented by up
  to three spaces, and leaves out a line that starts with `#` inside an HTML
  block. ([#403](https://github.com/alimanfoo/uncoded/pull/403))

### Fixed

- `uncoded sync` now reads a file under overlapping source or documentation
  roots once, so it warns about and counts a skipped file once.
  ([#408](https://github.com/alimanfoo/uncoded/pull/408))
- The docs map follows CommonMark's fence-closing rules, so a shorter fence or
  one with an info string no longer exposes headings inside a fenced code block.
  ([#403](https://github.com/alimanfoo/uncoded/pull/403))
- `uncoded refs` now finds every reference when valid whitespace separates a
  `def`, `async def` or `class` keyword from its name.
  ([#401](https://github.com/alimanfoo/uncoded/pull/401))
- `uncoded refs` retains the host from a file URI, so it reports the correct
  path for a project on a Windows network share.
  ([#398](https://github.com/alimanfoo/uncoded/pull/398))
- `uncoded refs` ignores a request from ty while waiting for a response, even
  when its id equals its own request's. It could fail with a traceback.
  ([#395](https://github.com/alimanfoo/uncoded/pull/395))

## [4.0.0](https://github.com/alimanfoo/uncoded/releases/tag/v4.0.0) — 2026-10-28

Before upgrading, follow
[Upgrading from version 3 to version 4](upgrading.md#from-version-3-to-version-4).

### Breaking

- On Windows, the paths that `uncoded refs` prints and the path comment in each
  stub use `/` to separate directories, as the namespace map and the docs map
  already do. So does every path in a message or a warning.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))
- `uncoded body` and `uncoded refs` find the project directory from the current
  directory, as the other commands do, and stop outside a project. They also
  stop when the `--in` file is outside the project directory. `uncoded refs` no
  longer looks for a project from the `--in` file's directory, and no longer
  falls back to the nearest `pyproject.toml`. The code navigation skill tells
  the agent to run them from the project directory.
  ([#325](https://github.com/alimanfoo/uncoded/pull/325))
- Stubs are laid out in the standard stub style that ruff and Black write for
  `.pyi` files. A function, a method, or a class with no members is one line
  that ends with `...`. No blank line separates consecutive functions, the
  members of a class, or consecutive classes with no members.
  ([#366](https://github.com/alimanfoo/uncoded/pull/366))
- A stub lists the symbols of each module body and class body in the order that
  the Python file defines them, not grouped by kind, so it shows which of two
  definitions of a name comes later.
  ([#367](https://github.com/alimanfoo/uncoded/pull/367))

### Added

- `uncoded --version` prints the installed version.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))
- The `required-version` setting names the one version of uncoded that a project
  uses. At any other version, every command stops, writes nothing, and gives the
  command that runs the required version. A value that is not one exact version,
  such as `"3.1"`, stops every command with a message that names the
  configuration file. ([#322](https://github.com/alimanfoo/uncoded/pull/322),
  [#326](https://github.com/alimanfoo/uncoded/pull/326))
- `uncoded init` sets uncoded up in a project. It writes `.uncoded.toml` with
  the roots that exist among `src`, `tests`, `README.md`, `AGENTS.md` and
  `docs`, and with the running version as the required version. It then runs
  `uncoded sync`, says which files to commit, and prints the lines that tell
  agents to load the navigation skills.
  ([#323](https://github.com/alimanfoo/uncoded/pull/323))

### Changed

- `uncoded sync` no longer removes skills under the names that earlier versions
  of uncoded gave them: `coherence-review`, `uncoded-coherence-review` and
  `uncoded-review`. It removed them on every run, so it deleted a skill of the
  user's own with one of those names. It removes only the skills that the
  running version generates, when the roots they belong with are gone. A project
  that still has a skill under an old name removes it as
  [Upgrading](upgrading.md) says.
  ([#337](https://github.com/alimanfoo/uncoded/pull/337))
- `uncoded body` and `uncoded refs` report an `--in` file that does not exist
  with the reason that the system gives, as they do for every other file that
  cannot be read: `Error: nope.py: No such file or directory`. They said
  `Error: nope.py: file not found.`
  ([#354](https://github.com/alimanfoo/uncoded/pull/354))

### Fixed

- What uncoded prints is UTF-8 on every system. It printed in the system's
  output encoding, so `uncoded body` printed a definition that holds `é` as
  bytes that are not UTF-8, such as on Windows, and stopped with a
  `UnicodeEncodeError` where that encoding lacks the character, such as ASCII.
  ([#368](https://github.com/alimanfoo/uncoded/pull/368))
- The uncoded skills use one word for each concept, such as "code index",
  "definition" and "project". They also stop listing directories and files among
  the symbols in the namespace map.
  ([#344](https://github.com/alimanfoo/uncoded/pull/344))
- The documentation navigation skill and the docs map's header say which heading
  a " (N)" suffix in the docs map marks: the Nth heading with the same text
  under one parent. The skill said that every heading in the docs map is literal
  text, and the header said to take the Nth match of the heading's text, which
  finds the wrong heading when the same text comes earlier elsewhere in the
  file. ([#344](https://github.com/alimanfoo/uncoded/pull/344))
- `uncoded body` prints a definition with the line endings that it has in the
  file. It printed every line ending as LF, and on Windows as CRLF, so an edit
  tool given the printed text could fail to find it in the file.
  ([#342](https://github.com/alimanfoo/uncoded/pull/342))
- `uncoded body` prints the definition when a form feed or a Unicode line
  separator, such as `\u2028` in a string, comes before the definition's end. It
  counted those characters as line breaks, which Python does not, so it printed
  the wrong lines. ([#342](https://github.com/alimanfoo/uncoded/pull/342))
- When a name is defined twice in one module body, the namespace map shows the
  later symbol, and `uncoded body` and `uncoded refs` find no member of a class
  that a later function, assignment or `type` statement redefines. The map
  showed a function over a class, and a class over an assignment, whatever the
  order. `uncoded body` and `uncoded refs` used the class.
  ([#341](https://github.com/alimanfoo/uncoded/pull/341))
- `uncoded refs` prints the symbol's definition and each import of it, as well
  as each use of it. It printed only the uses, so a symbol whose only reference
  was an import looked unused. The code navigation skill tells the agent to
  delete a symbol only when it is unused.
  ([#334](https://github.com/alimanfoo/uncoded/pull/334))
- When ty fails, `uncoded refs` says that ty failed and passes on what ty and
  `uvx` wrote about why, such as that ty could not be fetched. It discarded that
  output, and a ty that stopped early, or a `uvx` that could not start, could be
  reported as a fault in the `--in` file.
  ([#335](https://github.com/alimanfoo/uncoded/pull/335))
- When a source root is removed from the configuration while another source root
  stays, `uncoded sync` removes the removed root's stubs, and `uncoded check`
  counts them as files that would change. Both left the stubs alone, so
  `uncoded check` said that the index was current while an agent could still
  read the stub of a file that was no longer indexed.
  ([#339](https://github.com/alimanfoo/uncoded/pull/339))
- `uncoded sync` and `uncoded check` end their warnings about the files they
  skipped with a line that says how many files they skipped. A skip was easy to
  miss among the other lines, such as in the output of a pre-commit hook. The
  exit status is still `0`.
  ([#329](https://github.com/alimanfoo/uncoded/pull/329))
- When a configuration file is not valid TOML or a setting has the wrong type,
  every command names the file and the problem in one line, exits with status
  `1` and writes nothing. These gave a Python traceback, or a message that
  misled. A `pyproject.toml` on the way up to the configuration file that is not
  valid TOML stops the command too.
  ([#326](https://github.com/alimanfoo/uncoded/pull/326))
- `uncoded sync` and `uncoded check` check every root before they write
  anything. A doc root that could not be used was found only after the code
  index and the installed skill files were written. The message names the
  configuration file, the setting and the root, and says whether the root does
  not exist, is the wrong kind, or is outside the project directory. A root that
  did not exist was reported as "not a directory".
  ([#328](https://github.com/alimanfoo/uncoded/pull/328))
- When `uncoded sync` or `uncoded check` cannot read, write or remove a
  generated file, or `uncoded init` cannot write the configuration file, the
  command says in one line which file, what it could not do, and why, and exits
  with status `1`. This gave a Python traceback.
  ([#331](https://github.com/alimanfoo/uncoded/pull/331))
- `uncoded body` and `uncoded refs` stop when two files in one directory both
  configure uncoded, as the other commands already do.
  ([#322](https://github.com/alimanfoo/uncoded/pull/322))
- `uncoded refs` runs ty 0.0.92, in place of 0.0.53, and finds references that
  the older ty missed. ([#308](https://github.com/alimanfoo/uncoded/pull/308))
- `uncoded refs` on Windows prints each reference's path relative to the current
  directory, in place of a path that names no file.
  ([#312](https://github.com/alimanfoo/uncoded/pull/312))
- The search for the configuration file passes over a `pyproject.toml` without a
  `[tool.uncoded]` table, so a Python package's own `pyproject.toml` inside the
  project no longer hides the configuration file above it.
  ([#321](https://github.com/alimanfoo/uncoded/pull/321))
- The navigation skills tell the agent to run `uncoded sync` before it reads the
  namespace map or the docs map, and whenever it notices that something else has
  changed files, such as a pull or a checkout. They told it to run
  `uncoded sync` only when a map was missing, so an agent could read a map that
  was stale. ([#333](https://github.com/alimanfoo/uncoded/pull/333))

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
