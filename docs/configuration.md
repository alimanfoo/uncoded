# Configuration

Use one configuration file in the project directory. Choose the directories
containing Python code and the files or directories containing Markdown docs.
[`uncoded init`](getting-started.md) writes `.uncoded.toml`, and the developer
can edit it afterwards.

## Choose a configuration file

For a standalone configuration, use `.uncoded.toml`:

```toml title=".uncoded.toml"
source-roots = ["src", "tests"]
doc-roots = ["README.md", "docs"]
```

To keep the settings in `pyproject.toml`, add a section there instead:

```toml title="pyproject.toml"
[tool.uncoded]
source-roots = ["src", "tests"]
doc-roots = ["README.md", "docs"]
```

Both formats work in Python and non-Python projects. At least one root list must
be non-empty. Either kind of root can be configured on its own.

## Settings

| Setting        | Accepts                               | Effect                                 |
| -------------- | ------------------------------------- | -------------------------------------- |
| `source-roots` | Directories                           | Indexes Python symbols and signatures. |
| `doc-roots`    | Directories or individual `.md` files | Indexes Markdown headings.             |

Every path is relative to the configuration file's directory and must exist.
Paths that resolve outside that directory are rejected, including through
symbolic links.

uncoded searches upwards from the current directory and uses the nearest
configuration file. A `pyproject.toml` without `[tool.uncoded]` is not a
configuration file, so the search passes over it. If both files in one directory
configure uncoded, the command fails. Keep the settings in one file.

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
