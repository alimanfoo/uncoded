# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords,
skim the first few lines of files, and fill gaps from pretraining rather than
reading the actual code. The result is plausible-looking output built on a
hallucinated understanding of code that's sitting right there, unread.

**uncoded** builds a static navigation index so agents can orient themselves
at the start of a task and navigate deterministically to what they need —
no guessing, no grep.

> **Early software.** The index format and CLI are still settling.

## What it generates

Running `uncoded` produces two things under `.uncoded/`:

**`namespace.yaml`** — a hierarchical YAML file listing every public symbol:
directories, files, classes (with attributes and methods), functions. Covers
all configured source roots. An agent can load this at the start of a task
and immediately know the full vocabulary of the codebase.

**`stubs/`** — one `.pyi` stub per source file, with imports, full signatures
(parameter names, types, return types), first-sentence docstrings, and an
`L<start>-<end>` line range on every definition. Includes private symbols too,
so an agent can follow a call into implementation detail without grepping.

`uncoded` also injects a navigation protocol into `CLAUDE.md`, so agents
working in the repo pick up the instructions automatically.

## Install

```
pip install git+https://github.com/alimanfoo/uncoded
```

Or with uv:

```
uv add git+https://github.com/alimanfoo/uncoded
```

## Configure

Add a `[tool.uncoded]` section to your `pyproject.toml`:

```toml
[tool.uncoded]
source-roots = ["src", "tests"]
```

## Use

```
uncoded
```

That's it. Run it from the repo root. It reads `pyproject.toml` to find your
source roots, builds the index, and updates `CLAUDE.md`.

Commit the generated `.uncoded/` directory and `CLAUDE.md` so agents working
in the repo always have a current index.

## Keep it current with pre-commit

Add `uncoded` as a pre-commit hook so the index stays in sync automatically:

```yaml
- repo: local
  hooks:
    - id: uncoded
      name: uncoded
      entry: uncoded
      language: system
      pass_filenames: false
```

Like `ruff format`: if `uncoded` modifies any files, the commit fails and you
stage the updated index before committing again. CI runs `pre-commit run
--all-files` to verify the index is up to date.

## How agents use it

When `uncoded` is set up, a navigation section is automatically maintained in
`CLAUDE.md`. Agents following that protocol:

1. Read `.uncoded/namespace.yaml` to orient — every public symbol, at a glance.
2. Read the relevant `.pyi` stubs to understand signatures and locate line ranges.
3. Read only the source lines they need, using the `L<start>-<end>` ranges from the stubs.

Three reads to navigate to any symbol in the codebase. No grep.

## Using uncoded with a language server

Cross-file operations — find references, rename, check whether a symbol is
still used — are better served by a language server than by grep. Uncoded's
map supplies the `name_path` and `relative_path` these tools take as input.

The recommended setup is [oraios/serena][serena] as the MCP bridge with
[astral-sh/ty][ty] as the Python language-server backend. Serena launches
via `uvx`, so there's nothing to install globally; ty is downloaded by
Serena on first use.

For Claude Code, add `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from", "serena-agent==1.1.2",
        "serena", "start-mcp-server",
        "--context", "claude-code",
        "--transport", "stdio",
        "--project-from-cwd",
        "--open-web-dashboard", "false"
      ]
    }
  }
}
```

(Replace `claude-code` with your client's context name if different.)

And `.serena/project.yml` to pick ty as the backend:

```yaml
project_name: "<your-project>"
languages: ["python_ty"]
ignored_paths:
  - ".uncoded"
excluded_tools:
  - execute_shell_command
```

`languages: ["python_ty"]` selects ty over Serena's default (pyright); ty
handles src-layout repos natively, so no `venvPath` / `extraPaths` config
is needed. `ignored_paths` keeps Serena out of uncoded's generated stubs —
otherwise a rename would silently rewrite them. `excluded_tools` drops
Serena's `execute_shell_command`, which duplicates the shell access your
MCP client already exposes.

For Claude Code, commit `.claude/settings.json` to auto-enable the Serena
server and allowlist its read-only navigation tools:

```json
{
  "enabledMcpjsonServers": ["serena"],
  "permissions": {
    "allow": [
      "mcp__serena__find_symbol",
      "mcp__serena__find_referencing_symbols",
      "mcp__serena__get_symbols_overview"
    ]
  }
}
```

[serena]: https://github.com/oraios/serena
[ty]: https://github.com/astral-sh/ty

## Dev setup

Clone, install dependencies, and wire up the pre-commit hooks:

```
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync --extra dev
uv run pre-commit install
```

Run the tests:

```
uv run pytest
```

Run all checks (the same suite CI runs):

```
uv run pre-commit run --all-files
```
