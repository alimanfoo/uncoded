# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords, skim
the first few lines of files, and fill gaps from pretraining rather than reading
the actual code. The result is plausible-looking output built on a hallucinated
understanding of the code.

**uncoded** builds a static navigation index for the codebase. Agents load it at
the start of a task and navigate directly to what they need, without guessing or
grepping.

It also ships `uncoded body` to read symbol bodies and `uncoded refs` to find
every reference to a symbol. References cover callers, dead-symbol checks, and
the full set of sites to update before a rename.

## What it generates

Running `uncoded sync` produces:

**`.uncoded/namespace.yaml`**: a hierarchical YAML file listing every symbol:
directories, files, classes (with attributes and methods), functions. Covers all
configured source roots. An agent can load this at the start of a task and
immediately know the full vocabulary of the codebase.

**`.uncoded/stubs/`**: one `.pyi` stub per source file, with imports, full
signatures (parameter names, types, return types), module constants, and class
attributes.

**`.uncoded/docs.yaml`**: a heading outline of configured Markdown files. Each
file nests its `#`-prefixed headings as keys. Leaf headings map to null. Agents
load this to orient to the documentation. They then navigate to a heading with
`Read` or `grep`. uncoded generates it only when `doc-roots` is configured. It
is an outline only. `uncoded body`, `uncoded refs`, and stubs do not apply to
Markdown.

**`.uncoded/.gitignore`**: a local ignore rule for the whole `.uncoded/`
directory, including the rule itself. Generated indexes therefore stay out of
Git by default.

**Skills**, written to both `.claude/skills/` and `.agents/skills/`:

- **`uncoded-code-navigation`**: the code dispatch rule: load `namespace.yaml`
  first, read `.pyi` stubs before source, use `uncoded body` and `uncoded refs`
  for symbol operations. Generated when `source-roots` is configured.
- **`uncoded-doc-navigation`**: the docs navigation rule: load `docs.yaml` at
  session start, then use `Read` or `grep` to reach a heading. Generated when
  `doc-roots` is configured.
- **`uncoded-consistency-review`**: a semantic consistency review that reports
  concrete disagreements between claims about the same concept (see
  [Semantic consistency review](#semantic-consistency-review)). Generated when
  `source-roots` is configured.

Add these lines to your `AGENTS.md` or `CLAUDE.md` to load the navigation skills
every session. Skills are on-demand by default. Tying the load to an action
agents are about to take prompts them to act on it:

```text
## Before you start

- Load the `uncoded-code-navigation` skill once per session, before searching, reading or editing any code.
- Load the `uncoded-doc-navigation` skill once per session, before searching, reading or editing any docs.
```

## Install uv

uncoded runs via [uv](https://docs.astral.sh/uv/). Install uv if you don't
already have it. No separate uncoded install is needed. `uvx` runs it from PyPI
on demand.

## Configure

Add a `[tool.uncoded]` section to your `pyproject.toml`:

```toml
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["docs", "README.md"]  # dirs walked for *.md, or individual .md files
```

`source-roots` and `doc-roots` are each optional. At least one must be set.
`source-roots` drives the code index (namespace.yaml + stubs). `doc-roots`
drives the doc index (docs.yaml). Entries in `doc-roots` can be directories (all
`*.md` files walked recursively) or individual `.md` files.

**Non-Python repos** can use `.uncoded.toml` in the project root instead, with
the same keys at the top level. No `[tool.uncoded]` wrapper is needed:

```toml
doc-roots = ["docs"]
```

`pyproject.toml` takes precedence over a sibling `.uncoded.toml` only when it
carries a `[tool.uncoded]` section. If both files configure uncoded in the same
directory, `uncoded` reports a configuration error. Configure in one file only.

Across directories, the nearer file wins. uncoded never reads either file from
inside the `.uncoded/` directory.

## Use

```sh
uvx uncoded sync
```

Run `uvx uncoded sync` from the repo root. It reads `pyproject.toml` (or
`.uncoded.toml`) to find your configured roots and builds the index and skill
files. Commit the generated skill files so that agents can load them in a fresh
checkout. The generated `.uncoded/.gitignore` keeps the index itself local.

If an existing repository already tracks `.uncoded/`, remove the directory from
Git's index once. The files stay on disk, and the generated ignore rule keeps
them out of later commits:

```sh
git rm -r --cached .uncoded
uvx uncoded sync
```

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

The hook regenerates the ignored local index before every commit. If a skill
template changed, the hook also updates its tracked generated skill files; stage
those files and commit again.

You can also run `pre-commit run --all-files` in CI to verify that index
generation succeeds and the tracked skill files are current.

## Verify the index is fresh

Use the `check` subcommand for scripted checks that must not modify the working
tree:

```sh
uvx uncoded check
```

It runs the same pipeline but writes nothing. It exits 0 if every generated file
is byte-identical to what a rebuild would produce. It exits 1 otherwise,
printing which files would change. Run `sync` first in a fresh checkout, because
the ignored local index does not come from Git.

## Retrieve a symbol body

Use the `body` subcommand when you need a symbol's implementation, not just its
signature from the stub:

```sh
uvx uncoded body <name_path> --in <relative_path>
```

`name_path` is a slash-separated path: one segment (`fn`) for a top-level
symbol, two for a class member (`Class/method`). `--in` is the source file's
path (relative to cwd). The command prints the source text of the symbol to
stdout, byte-identical to what's on disk. No reformatting, no `ast.unparse`
normalisation.

For example, to retrieve the body of `resolve_body` from `src/uncoded/body.py`:

```sh
uvx uncoded body resolve_body --in src/uncoded/body.py
```

## Find references to a symbol

Use the `refs` subcommand for impact analysis. Run it before a rename, signature
change, or delete. Run it also to confirm a symbol is dead before removing it:

```sh
uvx uncoded refs <name_path> --in <relative_path>
```

`name_path` follows the same convention as `body`: one segment for a top-level
symbol, two for a class member (`Class/method`).

Output is one reference per line as `<path>:<line>:<col>`. Line and column are
1-indexed. Results are sorted by path, then line, then column. It exits 0 on
success. Empty output means no references.

For example, to find all callers of `resolve_body`:

```sh
uvx uncoded refs resolve_body --in src/uncoded/body.py
```

## How agents use it

Agents load the navigation skills and follow this protocol once `uncoded` is set
up:

1. Load the orientation artefacts. Read `.uncoded/namespace.yaml` to see every
   symbol at a glance. When `doc-roots` is configured, also read
   `.uncoded/docs.yaml`, the heading outline of all docs. Headings are literal
   text. Use `Read` or `grep` to navigate to a section.
2. Read the relevant `.pyi` stubs to understand imports, signatures, constants,
   and class members.
3. Run `uvx uncoded body <name_path> --in <relative_path>` when they need
   implementation detail for a specific symbol.
4. Run `uvx uncoded refs <name_path> --in <relative_path>` to find every
   reference to a symbol: callers, dead-symbol checks. See
   [Find references to a symbol](#find-references-to-a-symbol) for detail.
5. Edit a symbol using `Edit` with `uncoded body`'s output as `old_string`.
6. Rename across the codebase using `uncoded refs` to enumerate every site, then
   `Edit` at each.
7. Safely delete by running `uncoded refs` first. The output must be empty. Then
   `Edit` to remove.
8. Run `uvx uncoded sync` after every source or indexed documentation change,
   before using the index again.

Each tool owns one job. `uncoded` provides the stable map and signature index,
code through `namespace.yaml` and docs through `docs.yaml`. `uncoded body`
resolves a symbol's source body. `uncoded refs` maps every reference. Agents do
not grep, guess line numbers, or do offset arithmetic.

## Semantic consistency review

A codebase can make conflicting claims about one concept through competing
names, stale docstrings, mismatched signatures, or behaviour that no longer
matches a symbol's name.

`uncoded sync` installs an `/uncoded-consistency-review` skill that checks for
semantic and naming inconsistencies supported by concrete evidence.

Invoke the skill by name:

- Claude Code: `/uncoded-consistency-review`
- Codex: `$uncoded-consistency-review`

The review first checks vocabulary across the namespace, then checks symbol
contracts across names, signatures, docstrings, and behaviour. Every finding
quotes two claims about the same concept, explains how they differ, and explains
why they should agree. The review retrieves symbol bodies only when it needs a
docstring or implementation to confirm a candidate.

The skill returns its Markdown report directly. It does not modify the
repository or report general design and hygiene concerns that do not establish a
semantic inconsistency.

## Upgrading from v1

Version 2.0.0 replaces injection with skills. In v1, `uncoded sync` always
injected navigation guidance into `AGENTS.md`/`CLAUDE.md`. In v2 it ships as
on-demand skills. Agents load them when relevant. Four manual steps after
upgrading:

1. **Remove old marker blocks** from your `AGENTS.md` and `CLAUDE.md`. Look for
   and delete these blocks:

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

2. **Update any skill pointer** that references `coherence-review`,
   `uncoded-review`, or `uncoded-coherence-review` to
   `uncoded-consistency-review`. The skill now names its semantic consistency
   focus directly.

3. **Remove the `instruction-files` config key** if your `pyproject.toml` or
   `.uncoded.toml` has it. uncoded no longer reads this key. Leaving it in place
   causes no error.

4. **Restore always-on navigation** if you want v1 behaviour back. Add the
   "Before you start" lines from [What it generates](#what-it-generates) to your
   `AGENTS.md` and `CLAUDE.md`.

## Contributing

See [AGENTS.md](https://github.com/alimanfoo/uncoded/blob/main/AGENTS.md).
