# Command reference

Run the published tool with `uvx uncoded`. Contributors to _uncoded_ use
`uv run uncoded` so that commands execute the code in their checkout.

## `sync`

Build or refresh every configured index and navigation skill:

```sh
uvx uncoded sync
```

The command finds the nearest configuration file by walking up from the current
directory. It anchors all reads and writes at that file's directory, so running
it from a subdirectory produces the same output as running it from the project
root.

`sync` skips Python or Markdown files that it cannot decode and prints one
warning for each skipped file. Configuration errors and invalid roots exit with
status 1.

## `check`

Verify the index without changing any file:

```sh
uvx uncoded check
```

The command runs the same pipeline as `sync`. It exits with status 0 when every
generated file matches a fresh build, or status 1 when any file would be
created, updated, or removed. Run `sync` first in a fresh checkout because the
local index is not committed.

## `body`

Print one symbol's source body exactly as it appears in its file:

```sh
uvx uncoded body resolve_body --in src/uncoded/body.py
uvx uncoded body NamePath/parse --in src/uncoded/resolver.py
```

The name path has one segment for a top-level function, class, module
assignment, or PEP 695 type alias. Use `Class/member` for a method or class
attribute. Deeper paths and empty segments are not supported. The `--in` path is
resolved from the current working directory. The output goes to standard output
without normalizing or reformatting the source.

The command exits with status 1 when the file cannot be read or parsed, the
symbol does not exist, or the name path is unsupported.

## `refs`

Print every reference to one symbol:

```sh
uvx uncoded refs resolve_body --in src/uncoded/body.py
uvx uncoded refs NamePath/parse --in src/uncoded/resolver.py
```

Each result has the form `path:line:column`, with one-based positions, sorted by
path and position. Paths under the current directory are relative; other paths
are absolute. No output with status 0 means that the symbol has no references.
The `--in` path follows the same current-directory rule as `body`.

`refs` runs the pinned `ty` language server through `uvx`. The first call may
therefore download `ty`, and `uvx` must be available on `PATH`.
