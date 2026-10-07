# Architecture

_uncoded_ builds independent code and documentation indexes from one project
configuration. The command-line module coordinates both paths.

## Sync pipeline

`config.py` finds the nearest configuration and turns its paths into a `Config`.
`cli.py` validates that every root stays within the project and then dispatches
the configured work.

The code path performs these steps:

1. `extract.py` walks the source roots and extracts a `ModuleInfo` from each
   parseable Python file that contains indexed symbols.
2. `namespace_map.py` renders the module hierarchy into
   `.uncoded/namespace.yaml`.
3. `stubs.py` extracts signatures and assignments, then writes a mirrored `.pyi`
   tree under `.uncoded/stubs/`.
4. `skill.py` writes the code navigation and consistency review skills.

The documentation path performs these steps:

1. `docs_map.py` walks the documentation roots and extracts ATX headings.
2. The module renders the hierarchy into `.uncoded/docs.yaml`.
3. `skill.py` writes the documentation navigation skill.

`sync.py` owns idempotent writes and removals for both paths. In check mode it
reports the changes without mutating the filesystem.

## Symbol tools

`resolver.py` maps a `NamePath` to an abstract syntax tree node and its source
position. `body.py` uses the node's source lines to return the byte-identical
symbol body.

`refs.py` sends the resolved source position to a one-shot `ty` language server
and converts the returned locations into sorted, one-based references. The
language server owns semantic reference resolution; _uncoded_ owns the stable
command and output format.

The generated navigation skills are package resources and repository outputs at
the same time. `skill.py` renders the packaged Markdown into both supported
agent directories. The shared provenance marker in `markers.py` identifies all
generated output.

## Path boundary

Generated index paths are always anchored at the configuration file's parent,
even when the command runs in a subdirectory. A configured root cannot escape
that project root after path resolution.
