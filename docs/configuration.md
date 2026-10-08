# Configuration

Use one configuration file in your repository root. Choose the directories
containing Python code and the files or directories containing Markdown docs.

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

Both formats work in Python and non-Python repositories. At least one root list
must be non-empty. You can configure either type on its own.

## Settings

| Setting        | Accepted paths                        | Indexed content                |
| -------------- | ------------------------------------- | ------------------------------ |
| `source-roots` | Directories                           | Python symbols and signatures. |
| `doc-roots`    | Directories or individual `.md` files | Markdown headings.             |

Every path is relative to the configuration file's directory and must exist.
Paths that resolve outside that directory are rejected, including through
symbolic links.

uncoded searches upwards from the current directory and uses the nearest
configuration. In one directory, `.uncoded.toml` takes precedence over a
`pyproject.toml` without `[tool.uncoded]`. If both files configure uncoded, the
command fails. Keep the settings in one file.

## Generated files

| Output                                        | When generated         | Commit it? |
| --------------------------------------------- | ---------------------- | ---------- |
| `.uncoded/namespace.yaml`                     | `source-roots` is set. | No.        |
| `.uncoded/stubs/`                             | `source-roots` is set. | No.        |
| `.uncoded/docs.yaml`                          | `doc-roots` is set.    | No.        |
| Code navigation and consistency review skills | `source-roots` is set. | Yes.       |
| Documentation navigation skill                | `doc-roots` is set.    | Yes.       |

The index's generated `.gitignore` keeps `.uncoded/` out of Git. Skills are
written to both `.agents/skills/` and `.claude/skills/`.

When you remove a root type and run `sync`, uncoded removes that type's index
and skills. Every generated file has a provenance marker. Change generated files
by running `sync`, rather than editing them by hand.
