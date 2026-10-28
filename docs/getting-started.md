# Get started

Set uncoded up in your repository with one command, then tell your agent to use
the index. You need
[uv](https://docs.astral.sh/uv/getting-started/installation/). `uvx` runs
uncoded on demand; there is no separate install step.

<span id="install-uv"></span> <span id="choose-a-configuration-file"></span>
<span id="build-the-index"></span>

## 1. Set uncoded up

Run from the directory that is to be the project directory, usually the root of
your repository:

```sh
uvx uncoded init
```

`uncoded init` writes `.uncoded.toml`, the configuration file, in the project
directory. For a repository that has all the roots it looks for, the file is:

```toml title=".uncoded.toml"
source-roots = ["src", "tests"]
doc-roots = ["README.md", "AGENTS.md", "docs"]
required-version = "3.1.0"
```

The source roots are whichever of `src` and `tests` exist, and `source-roots`
indexes Python files. The doc roots are whichever of `README.md`, `AGENTS.md`
and `docs` exist, and `doc-roots` indexes Markdown headings. The required
version is the version of uncoded that ran. Every uncoded command in the project
refuses to run at any other version, and gives the command that runs the
required one, such as `uvx uncoded@3.1.0 sync`.

`uncoded init` then builds the index and the skills, and prints the files it
writes. With both kinds of root, you will find:

| Output                                  | Purpose                                                 |
| --------------------------------------- | ------------------------------------------------------- |
| `.uncoded/namespace.yaml`               | Lists Python symbols and their locations.               |
| `.uncoded/stubs/`                       | Records imports, signatures, constants, and attributes. |
| `.uncoded/docs.yaml`                    | Lists Markdown files and headings.                      |
| `.agents/skills/` and `.claude/skills/` | Give agents the navigation instructions.                |

Check the roots in `.uncoded.toml`. If your code or docs live elsewhere, edit
the roots and run `uvx uncoded init` again. It leaves the configuration file as
it is, and rebuilds the index from it.

If none of those directories and files exist, `uncoded init` writes nothing and
says so. Write `.uncoded.toml` by hand, as [Configuration](configuration.md)
shows, and run `uvx uncoded init` again.

<span id="tell-agents-to-use-the-skills"></span>

## 2. Tell your agent to use it

`uncoded init` ends by printing the lines to add to your repository's
`AGENTS.md` or `CLAUDE.md`. They tell agents to load the navigation skills at
the start of every session, one line for each kind of root. Without them, agents
load the uncoded skills only when they choose to. Add them to the file that your
agents read.

Running `uvx uncoded init` again prints the lines for the roots that the
configuration file names now.

## 3. Commit

Commit `.uncoded.toml`, the installed skill files, and the edited `AGENTS.md` or
`CLAUDE.md`. The `.uncoded/` index stays local and is ignored by Git.

## 4. Try a task

Start a new agent session in the repository and ask:

```text title="Example prompt"
Explain this repository using the uncoded navigation skills.
Read the index first, then show me one function or documentation section
that explains how the project works.
```

For Python code, the agent should move from `.uncoded/namespace.yaml` to a
matching stub and then to `uncoded body` as it needs more detail. The agent can
stop after the map or stub when that view answers the question. For
documentation, it should load `.uncoded/docs.yaml` and read the relevant
section.

<span id="keep-the-index-current"></span>

The agent runs `uncoded sync` to keep the index current as it works.
[Keep the index current](keeping-current.md) explains how, and how to add a
pre-commit hook.

See [Configuration](configuration.md) to use `pyproject.toml` or change the
indexed paths.
