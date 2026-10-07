# Configuration

_uncoded_ searches from the current directory towards the filesystem root. The
first directory that contains a configuration file becomes the project root, and
every configured path is resolved from that directory.

## Python projects

Use `[tool.uncoded]` in `pyproject.toml`:

```toml
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["README.md", "AGENTS.md", "docs"]
```

## Other projects

Use top-level settings in `.uncoded.toml`:

```toml
source-roots = ["tools"]
doc-roots = ["docs"]
```

A `.uncoded.toml` file beside a `pyproject.toml` without an `uncoded` section
wins in that directory. If both files configure _uncoded_ in the same directory,
the command fails and asks you to keep the settings in one file.

## Settings

| Setting        | Accepted roots                                                | Generated output                                                                                    |
| -------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `source-roots` | Directories inside the project root                           | `.uncoded/namespace.yaml`, `.uncoded/stubs/`, and the code navigation and consistency review skills |
| `doc-roots`    | Directories or individual `.md` files inside the project root | `.uncoded/docs.yaml` and the documentation navigation skill                                         |

Directories in `source-roots` are walked for Python files. Directories in
`doc-roots` are walked for Markdown files. A root that resolves outside the
project root is rejected, including a path that leaves the project through a
symbolic link.

Each root type is independent. If you remove `source-roots` and run `sync`,
_uncoded_ removes the code index and code-gated skills. The same rule applies to
`doc-roots` and the documentation index. An empty configuration is an error
because it has nothing to index.

## Generated files

The `.uncoded/` directory is local build output. Its generated `.gitignore`
contains `*`, which leaves the whole directory untracked.

The skill files are repository content. Commit the generated files under
`.agents/skills/` and `.claude/skills/` so that agents can load the workflow
without first installing _uncoded_. Every generated file carries a provenance
marker and should be changed by running `sync`, not by hand.
