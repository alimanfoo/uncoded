# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords,
skim the first few lines of files, and fill gaps from pretraining rather than
reading the actual code. The result is plausible-looking output built on a
hallucinated understanding of code that's sitting right there, unread.

**uncoded** builds a static navigation index so agents can orient themselves
at the start of a task and navigate deterministically to what they need —
no guessing, no grep.

It also ships `uncoded body` to read symbol bodies and `uncoded refs` for
finding every reference to a symbol — callers, dead-symbol checks,
pre-rename footprint.

## What it generates

Running `uncoded sync` produces:

**`.uncoded/namespace.yaml`** — a hierarchical YAML file listing every symbol:
directories, files, classes (with attributes and methods), functions. Covers
all configured source roots. An agent can load this at the start of a task
and immediately know the full vocabulary of the codebase.

**`.uncoded/stubs/`** — one `.pyi` stub per source file, with imports, full
signatures (parameter names, types, return types), module constants, and
class attributes.

**`.uncoded/docs.yaml`** — a heading outline of configured Markdown files.
Each file nests its ATX headings as keys; leaf headings map to null. Agents
load this to orient to the documentation, then navigate to a heading with
`Read` or `grep`. Generated only when `doc-roots` is configured. Outline
only — `uncoded body`, `uncoded refs`, and stubs do not apply to Markdown.

**Skills** — written to both `.claude/skills/` and `.agents/skills/`:

- **`uncoded-code-navigation`** — the code dispatch rule: load `namespace.yaml`
  first, read `.pyi` stubs before source, use `uncoded body` and `uncoded refs`
  for symbol operations. Generated when `source-roots` is configured.
- **`uncoded-doc-navigation`** — the docs navigation rule: load `docs.yaml` at
  session start, then use `Read` or `grep` to reach a heading. Generated when
  `doc-roots` is configured.
- **`uncoded-coherence-review`** — a structured diagnostic sweep for naming drift
  and incoherence (see [Coherence review](#coherence-review)). Generated when
  `source-roots` is configured.

Skills are on-demand by default. To have the navigation skills loaded every
session, add one line to your `AGENTS.md` or `CLAUDE.md`:

```text
Always load the `uncoded-code-navigation` and `uncoded-doc-navigation` skills.
```

This is optional — agents can also load them on demand.

## Install uv

uncoded runs via [uv](https://docs.astral.sh/uv/). Install uv if you don't
already have it; no separate uncoded install is needed — `uvx` runs it
from PyPI on demand.

## Configure

Add a `[tool.uncoded]` section to your `pyproject.toml`:

```toml
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["docs", "README.md"]  # dirs walked for *.md, or individual .md files
```

`source-roots` and `doc-roots` are each optional; at least one must be set.
`source-roots` drives the code index (namespace.yaml + stubs). `doc-roots`
drives the doc index (docs.yaml). Entries in `doc-roots` can be directories
(all `*.md` files walked recursively) or individual `.md` files.

**Non-Python repos** can use `.uncoded.toml` in the project root instead,
with the same keys at the top level — no `[tool.uncoded]` wrapper needed:

```toml
doc-roots = ["docs"]
```

`pyproject.toml` takes precedence over a sibling `.uncoded.toml` only when it
carries a `[tool.uncoded]` section; a bare `pyproject.toml` does not shadow a
sibling `.uncoded.toml`. If both files configure uncoded in the same directory,
`uncoded` reports a configuration error — configure in one file only. Across
directories, the nearer file wins. Neither file is ever read from inside the
`.uncoded/` directory.

## Use

```sh
uvx uncoded sync
```

Run it from the repo root. It reads `pyproject.toml` (or `.uncoded.toml`)
to find your configured roots and builds the index and skill files.

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
      entry: uvx uncoded sync
      language: system
      pass_filenames: false
```

Like `ruff format`: if `uncoded sync` modifies any files, the commit
fails and you stage the updated index before committing again.

You can also set up your CI to run `pre-commit run --all-files` to verify
the index is up to date.

## Verify the index is fresh

For CI or scripted checks that must not modify the working tree, use
the `check` subcommand:

```sh
uvx uncoded check
```

It runs the same pipeline but writes nothing. Exits 0 if every generated
file is byte-identical to what a rebuild would produce, and 1 otherwise
— printing which files would change. A stale index is a silent failure
mode (agents read misleading names and signatures), so gating on this in
CI is worthwhile even alongside a pre-commit hook.

## Retrieve a symbol body

Use the `body` subcommand when you need a symbol's implementation, not just
its signature from the stub:

```sh
uvx uncoded body <name_path> --in <relative_path>
```

`name_path` is a slash-separated path: one segment (`fn`) for a top-level
symbol, two for a class member (`Class/method`). `--in` is the source file's
path (relative to cwd). The command prints the source text of the
symbol to stdout, byte-identical to what's on disk — no reformatting, no
`ast.unparse` normalisation.

For example, to retrieve the body of `resolve_body` from `src/uncoded/body.py`:

```sh
uvx uncoded body resolve_body --in src/uncoded/body.py
```

## Find references to a symbol

Use the `refs` subcommand for impact analysis: run it before a rename,
signature change, or delete, or to confirm a symbol is dead before removing it:

```sh
uvx uncoded refs <name_path> --in <relative_path>
```

`name_path` follows the same convention as `body`: one segment for a top-level
symbol, two for a class member (`Class/method`). Output is one reference per
line as `<rel_path>:<line>:<col>`, with line and column 1-indexed and results
sorted by path, then line, then column. Exits 0 on success; empty output
means no references.

For example, to find all callers of `resolve_body`:

```sh
uvx uncoded refs resolve_body --in src/uncoded/body.py
```

## How agents use it

When `uncoded` is set up, agents load the navigation skills and follow this protocol:

1. Load the orientation artefacts. Read `.uncoded/namespace.yaml` — every
   symbol, at a glance. When `doc-roots` is configured, also read
   `.uncoded/docs.yaml` — the heading outline of all docs. Headings are
   literal text; use `Read` or `grep` to navigate to a section.
2. Read the relevant `.pyi` stubs to understand imports, signatures,
   constants, and class members.
3. Run `uvx uncoded body <name_path> --in <relative_path>` when they
   need implementation detail for a specific symbol.
4. Run `uvx uncoded refs <name_path> --in <relative_path>` to find
   every reference to a symbol — callers, dead-symbol checks. See
   [Find references to a symbol](#find-references-to-a-symbol) for detail.
5. Edit a symbol using `Edit` with `uncoded body`'s output as `old_string`.
6. Rename across the codebase using `uncoded refs` to enumerate every site,
   then `Edit` at each.
7. Safely delete by running `uncoded refs` first — the output must be
   empty — then `Edit` to remove.

The split is deliberate: `uncoded` provides a stable map and signature index
(code through namespace.yaml, docs through docs.yaml); `uncoded body` resolves
a symbol's source body; `uncoded refs` maps every reference. No grep, no stale
line-number coordinates, no offset arithmetic.

## Coherence review

AI coding agents tend to leave codebases in an incoherent state: names that
no longer match behaviour, docstrings that describe stale signatures, dead
symbols, pattern changes applied in some places but not others. `uncoded sync`
installs an `/uncoded-coherence-review` skill that runs a structured diagnostic sweep to
find these problems.

Invoke it in Claude Code:

```text
/uncoded-coherence-review
```

The review works in four sweeps:

1. **Orient** — loads `namespace.yaml` and forms a vocabulary map.
2. **Lexical** — scans the namespace for naming inconsistency: concept
   duplication, qualifier accretion (`_v2`, `_legacy`, `_final`), vocabulary
   islands, name collision with drift.
3. **Promissory** — checks each public symbol's name / signature / docstring
   triple for internal disagreement. Names and signatures come from the
   stub; docstrings come from `uncoded body`.
4. **Structural** — checks for boundary violations (private symbols imported
   across modules), overgrown public surfaces, cross-domain imports, and
   zero-reference public symbols.

Output is a timestamped Markdown report saved to `.uncoded/reviews/`, with
verbatim evidence and a confidence level (high / medium / low) for each
finding. The review only reports — it proposes no fixes. The human decides
what to follow up.

## Dev setup

Clone, install dependencies, and wire up the pre-commit hooks:

```sh
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync --extra dev
uv run pre-commit install
```

Run the tests (branch coverage is enforced; see `[tool.coverage.report]` in
`pyproject.toml` for the threshold):

```sh
uv run pytest
```

To run a subset of tests without the coverage gate:

```sh
uv run pytest tests/test_stubs.py --no-cov
```

Run the same checks CI's lint job runs:

```sh
uv run pre-commit run --all-files
```

When testing local changes to uncoded, use `uv run uncoded ...` rather than
`uvx uncoded ...`. `uvx` always pulls the published package from PyPI; `uv run`
runs the local editable install. For example, after editing source files run
`uv run uncoded sync` to regenerate the index from the working tree.

This repo dogfoods uncoded: `.pre-commit-config.yaml` runs `uv run uncoded sync`
as a pre-commit hook. On each commit the hook regenerates
`.uncoded/namespace.yaml`, the stub files under `.uncoded/stubs/`,
`.uncoded/docs.yaml`, and the skill files under `.claude/skills/` and `.agents/skills/`.
If the hook modifies any of those files the commit fails — re-stage
the changes and commit again.

## Upgrading from v1

Version 2.0.0 replaces injection with skills. Three manual steps after upgrading:

1. **Remove old marker blocks** from your `AGENTS.md` and `CLAUDE.md`. Look
   for and delete these blocks:

   ```text
   <!-- uncoded:start ... -->
   ...
   <!-- uncoded:end -->
   ```

   and

   ```text
   <!-- uncoded:docs:start ... -->
   ...
   <!-- uncoded:docs:end -->
   ```

   uncoded no longer manages these sections. Leaving them in place is harmless
   but they are now dead markup.

2. **Update any skill pointer** that references `coherence-review` to
   `uncoded-coherence-review`. The coherence review skill was renamed with the
   `uncoded-` prefix to match the navigation skills.

3. **Remove the `instruction-files` config key** if your `pyproject.toml` or
   `.uncoded.toml` has it. uncoded no longer reads this key; leaving it in
   place causes no error.

## Releasing

GitHub releases publish to PyPI through `.github/workflows/publish.yml`.
The workflow uses PyPI Trusted Publishing, so it does not need a `PYPI_TOKEN`
or any other long-lived publishing secret.

The PyPI trusted publisher is configured for:

- PyPI project: `uncoded`
- Owner: `alimanfoo`
- Repository: `uncoded`
- Workflow: `publish.yml`
- Environment: `pypi`

To release, create and publish a GitHub release from the release tag. The
`published` release event builds the source distribution and wheel, then
uploads them to PyPI.
