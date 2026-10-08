# Architecture

uncoded builds static code and documentation indexes. The CLI reads the
configuration, validates roots, and coordinates extraction and file writes.

## Sync pipeline

| Module             | Responsibility                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------- |
| `config.py`        | Finds the nearest configuration and resolves the project root.                            |
| `cli.py`           | Validates roots and dispatches the configured work.                                       |
| `extract.py`       | Extracts symbols from parseable Python files.                                             |
| `namespace_map.py` | Renders the Python hierarchy as YAML.                                                     |
| `stubs.py`         | Extracts imports, signatures, and assignments into a mirrored `.pyi` tree.                |
| `docs_map.py`      | Extracts Markdown headings and renders their hierarchy as YAML.                           |
| `skill.py`         | Writes navigation and consistency review skills to both agent directories.                |
| `sync.py`          | Writes and removes files only when needed; reports changes without writing in check mode. |

Code and documentation indexes are independent. Removing a root type removes its
generated index and skills on the next sync.

The skill instructions ship as Markdown package resources. `skill.py` renders
them into repository skill files. `markers.py` defines the provenance marker
shared by every generated output.

## Symbol tools

`resolver.py` locates a named Python symbol in the abstract syntax tree and
records its source position. `body.py` uses that location to return the original
source text.

`refs.py` sends the position to a one-shot `ty` language server, then sorts and
formats the returned references. `ty` resolves the references; uncoded provides
the command and output format.

## Path boundary

`sync` and `check` anchor all generated files at the configuration file's parent
directory. Every configured root must remain inside that directory after
resolving symbolic links.

`body` and `refs` resolve their `--in` paths from the current working directory.
They can operate without a project configuration.
