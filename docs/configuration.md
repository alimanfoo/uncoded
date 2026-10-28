# Configuration

Use one configuration file in your project directory. Choose the directories
containing Python code and the files or directories containing Markdown docs.
[`uncoded init`](getting-started.md) writes `.uncoded.toml` for you, and you can
edit it afterwards.

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

| Setting            | Accepts                               | Effect                                          |
| ------------------ | ------------------------------------- | ----------------------------------------------- |
| `source-roots`     | Directories                           | Indexes Python symbols and signatures.          |
| `doc-roots`        | Directories or individual `.md` files | Indexes Markdown headings.                      |
| `required-version` | One exact version, such as `"3.1.0"`  | Refuses to run at any other version of uncoded. |

Every path is relative to the configuration file's directory and must exist.
Paths that resolve outside that directory are rejected, including through
symbolic links.

uncoded searches upwards from the current directory and uses the nearest
configuration file. A `pyproject.toml` without `[tool.uncoded]` is not a
configuration file, so the search passes over it. If both files in one directory
configure uncoded, the command fails. Keep the settings in one file.

## Require one version

To make every machine run the same version of uncoded in the project, set
`required-version` to one exact version:

```toml title=".uncoded.toml"
required-version = "3.1.0"
```

At any other version, every command stops before it changes anything. It says
which version the project requires, and gives the command that runs it, such as
`uvx uncoded@3.1.0 sync`. Without `required-version`, every version runs.

If a pre-commit hook runs uncoded, name the same version in the hook's `entry`,
such as `uvx uncoded@3.1.0 sync`. To upgrade, raise the version in both places.

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
