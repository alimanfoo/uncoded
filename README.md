# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords,
skim the first few lines of files, and fill gaps from pretraining rather than
reading the actual code. The result is plausible-looking output built on a
hallucinated understanding of code that's sitting right there, unread.

**uncoded** builds a static navigation index so agents can orient themselves
at the start of a task and navigate deterministically to what they need —
no guessing, no grep.

Additionally, **uncoded** provides some convenience for setting up your coding agent with a language server, so they can reliably find symbol usages and rename, edit, or delete symbols safely.

## What it generates

Running `uncoded sync` produces:

**`.uncoded/namespace.yaml`** — a hierarchical YAML file listing every symbol:
directories, files, classes (with attributes and methods), functions. Covers
all configured source roots. An agent can load this at the start of a task
and immediately know the full vocabulary of the codebase.

**`.uncoded/stubs/`** — one `.pyi` stub per source file, with imports, full
signatures (parameter names, types, return types), first-sentence docstrings,
module constants, and class attributes.

**`.claude/skills/coherence-review/SKILL.md`** and
**`.agents/skills/coherence-review/SKILL.md`** — a coherence review skill,
written to both Claude Code and Codex skill directories (see
[Coherence review](#coherence-review) below).

`uncoded` also injects a navigation protocol into `CLAUDE.md`/`AGENTS.md`, so agents
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
uncoded sync
```

Run it from the repo root. It reads `pyproject.toml` to find your source
roots, builds the index, and updates `CLAUDE.md`/`AGENTS.md`.

Commit the generated `.uncoded/` directory so agents working
in the repo always have a current index.

## Keep it current with pre-commit

Add `uncoded sync` as a pre-commit hook so the index stays in sync
automatically:

```yaml
- repo: local
  hooks:
    - id: uncoded
      name: uncoded
      entry: uncoded sync
      language: system
      pass_filenames: false
```

Like `ruff format`: if `uncoded sync` modifies any files, the commit
fails and you stage the updated index before committing again.

You can also set up your CI to run `pre-commit run --all-files` to verify the index is up to date.

## Verify the index is fresh

For CI or scripted checks that must not modify the working tree, use
the `check` subcommand:

```
uncoded check
```

It runs the same pipeline but writes nothing. Exits 0 if every generated
file is byte-identical to what a rebuild would produce, and 1 otherwise
— printing which files would change. A stale index is a silent failure
mode (agents read misleading names and signatures), so gating on this in
CI is worthwhile even alongside a pre-commit hook.

## How agents use it

When `uncoded` is set up, a navigation section is automatically maintained in
the configured instruction files (by default, `CLAUDE.md` and `AGENTS.md`).
Agents following that protocol:

1. Read `.uncoded/namespace.yaml` to orient — every symbol, at a glance.
2. Read the relevant `.pyi` stubs to understand imports, signatures, constants, class members, and docstring summaries.
3. Use Serena's `find_symbol(..., include_body=True)` when they need implementation detail for a specific symbol.

The split is deliberate: `uncoded` provides a stable map and semantic summary;
Serena resolves the current source body. No grep, no stale line-number
coordinates, no offset arithmetic.

## Coherence review

AI coding agents tend to leave codebases in an incoherent state: names that
no longer match behaviour, docstrings that describe stale signatures, dead
symbols, pattern changes applied in some places but not others. `uncoded sync`
installs a `/coherence-review` skill that runs a structured diagnostic sweep to
find these problems.

Invoke it in Claude Code:

```
/coherence-review
```

The review works in four sweeps:

1. **Orient** — loads `namespace.yaml` and forms a vocabulary map.
2. **Lexical** — scans the namespace for naming inconsistency: concept
   duplication, qualifier accretion (`_v2`, `_legacy`, `_final`), vocabulary
   islands, name collision with drift.
3. **Promissory** — reads stubs, checking each symbol's name / signature /
   docstring triple for internal disagreement.
4. **Structural** — checks for boundary violations (private symbols imported
   across modules), overgrown public surfaces, cross-domain imports, and
   zero-caller public symbols.

Output is a timestamped Markdown report saved to `.uncoded/reviews/`, with
verbatim evidence and a confidence level (high / medium / low) for each
finding. The review only reports — it proposes no fixes. The human decides
what to follow up.

## Using uncoded with a language server

Symbol-level operations — finding callers, reading or editing a single
symbol, renaming, safe deletion — are better served by a language server
than by grep and freeform text edits. Uncoded's map supplies the
`name_path` and `relative_path` these tools take as input.

The recommended setup is [oraios/serena][serena] as the MCP bridge with
[astral-sh/ty][ty] as the Python language-server backend. Serena launches
via `uvx`, so there's nothing to install globally; ty is downloaded by
Serena on first use.

### Setup

```
uv run uncoded setup-serena
```

Generates three files, tailored for Claude Code:

- **`.mcp.json`** — registers Serena as an MCP server, launched via `uvx`.
- **`.serena/project.yml`** — picks ty as the backend, ignores `.uncoded/`,
  drops the redundant `execute_shell_command`.
- **`.claude/settings.json`** — enables the Serena server and allowlists
  its navigation, edit, and memory tools.

Safe to re-run: JSON files merge into existing content (so pre-existing
MCP servers and permissions are preserved), and the Serena project YAML
is left alone once present. Restart your agent afterwards so the new
MCP server is picked up.

If you're not using Claude Code, the generated `.serena/project.yml` is
MCP-client-agnostic, and `.mcp.json` can serve as a starting point —
replace `claude-code` with your client's context name.

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
