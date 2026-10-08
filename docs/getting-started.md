# Getting started

_uncoded_ runs through [uv](https://docs.astral.sh/uv/). A repository needs a
configuration file, at least one root to index, and a short instruction that
tells agents to load the generated navigation skills.

## Install uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) before
running _uncoded_. `uvx` downloads and runs the published package on demand, so
_uncoded_ needs no separate installation.

## Choose a configuration file

If `pyproject.toml` should own the configuration, add an `uncoded` section:

```toml
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["README.md", "docs"]
```

`source-roots` selects Python files for the symbol index. `doc-roots` selects
Markdown files for the documentation outline. Either setting can be omitted, but
at least one must contain a root.

Use `.uncoded.toml` when the configuration should stand alone, including in a
Python repository. [Configuration](configuration.md) gives both file formats and
the rules for choosing between them.

## Build the index

Build the index:

```sh
uvx uncoded sync
```

The first run writes the local index under `.uncoded/` and writes navigation
skills under `.agents/skills/` and `.claude/skills/`. Commit the skill files so
that agents receive the navigation protocol in a fresh checkout. The generated
`.uncoded/.gitignore` keeps the index itself out of Git.

## Tell agents to use the skills

Add these instructions to the repository's `AGENTS.md` or `CLAUDE.md`:

```text
## Before you start

- Load the `uncoded-code-navigation` skill once per session, before searching, reading or editing any code.
- Load the `uncoded-doc-navigation` skill once per session, before searching, reading or editing any docs.
```

Keep the code navigation line only when `source-roots` is configured. Keep the
documentation navigation line only when `doc-roots` is configured.

## Keep the index current

Add a local pre-commit hook after formatters that may change indexed files:

```yaml
- repo: local
  hooks:
    - id: uncoded
      name: uncoded
      entry: uvx uncoded sync
      language: system
      always_run: true
      pass_filenames: false
```

Install the configured hooks once:

```sh
uvx pre-commit install
```

See [Agent workflow](agent-workflow.md) for the update sequence that agents
follow during a task.
