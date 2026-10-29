# Configuration

Keep uncoded's settings in `pyproject.toml` in the project directory. Choose the
directories containing Python code and the files or directories containing
Markdown docs. [`uncoded init`](getting-started.md) appends the table, and the
developer can edit it afterwards.

## Add the configuration table

Add this section to `pyproject.toml`:

```toml title="pyproject.toml"
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["README.md", "docs"]
```

At least one root list must be non-empty. Either kind of root can be configured
on its own.

## Settings

| Setting        | Accepts                               | Effect                                 |
| -------------- | ------------------------------------- | -------------------------------------- |
| `source-roots` | Directories                           | Indexes Python symbols and signatures. |
| `doc-roots`    | Directories or individual `.md` files | Indexes Markdown headings.             |

Every path is relative to the configuration file's directory and must exist.
Paths that resolve outside that directory are rejected, including through
symbolic links.

uncoded searches upwards from the current directory and uses the nearest
`pyproject.toml` with a `[tool.uncoded]` table. A `pyproject.toml` without that
table is not a configuration file, so the search passes over it.

## Generated files

| Output                                        | When generated               | Commit it? |
| --------------------------------------------- | ---------------------------- | ---------- |
| `.uncoded/namespace.yaml`                     | `source-roots` names a root. | No.        |
| `.uncoded/stubs/`                             | `source-roots` names a root. | No.        |
| `.uncoded/docs.yaml`                          | `doc-roots` names a root.    | No.        |
| Code navigation and consistency review skills | `source-roots` names a root. | Yes.       |
| Documentation navigation skill                | `doc-roots` names a root.    | Yes.       |

The generated `.uncoded/.gitignore` keeps `.uncoded/` out of Git. Skills are
written to both `.agents/skills/` and `.claude/skills/`.

When every root of one kind is removed, `sync` removes that part of the index,
and its skills. Every generated file has a provenance marker. Change generated
files by running `sync`, rather than editing them by hand.
