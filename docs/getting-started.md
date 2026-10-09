# Get started

Set up uncoded in your repository, then ask your agent to use the index. You
need [uv](https://docs.astral.sh/uv/getting-started/installation/). `uvx` runs
uncoded on demand; there is no separate install step.

<span id="install-uv"></span> <span id="choose-a-configuration-file"></span>

## 1. Choose what to index

Create `.uncoded.toml` in your repository root:

```toml title=".uncoded.toml"
source-roots = ["src", "tests"]
doc-roots = ["README.md", "docs"]
```

Replace these paths with directories and files that exist in your repository.
`source-roots` indexes Python files. `doc-roots` indexes Markdown headings.
Remove either line if you only need the other index.

<span id="build-the-index"></span>

## 2. Build the index

Run from your repository root:

```sh
uvx uncoded sync
```

The command prints the files it creates. With both root types configured, you
will find:

| Output                                  | Purpose                                                 |
| --------------------------------------- | ------------------------------------------------------- |
| `.uncoded/namespace.yaml`               | Lists Python symbols and their locations.               |
| `.uncoded/stubs/`                       | Records imports, signatures, constants, and attributes. |
| `.uncoded/docs.yaml`                    | Lists Markdown files and headings.                      |
| `.agents/skills/` and `.claude/skills/` | Give agents the navigation instructions.                |

Commit the generated skill files. The `.uncoded/` index stays local and is
ignored by Git.

<span id="tell-agents-to-use-the-skills"></span>

## 3. Tell your agent to use it

Add these instructions to your repository's `AGENTS.md` or `CLAUDE.md`:

```text title="Agent instructions"
## Before you start

- Load the `uncoded-code-navigation` skill once per session, before searching, reading or editing any code.
- Load the `uncoded-doc-navigation` skill once per session, before searching, reading or editing any docs.
```

Keep only the lines for the root types you configured.

## 4. Try a task

Start a new agent session in the repository and ask:

```text title="Example prompt"
Explain this repository using the uncoded navigation skills.
Read the index first, then show me one function or documentation section
that explains how the project works.
```

For Python code, the agent should load `.uncoded/namespace.yaml`, read a
matching stub, and run `uncoded body` for the function it chooses. For
documentation, it should load `.uncoded/docs.yaml` and read the relevant
section.

<span id="keep-the-index-current"></span>

When you change indexed code or docs, run `uvx uncoded sync` again before
navigating. [Keep the index current](keeping-current.md) explains how to
automate this with pre-commit.

See [Configuration](configuration.md) to use `pyproject.toml` or change the
indexed paths.
