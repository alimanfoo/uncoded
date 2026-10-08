# Commands

Run uncoded with `uvx uncoded`. Contributors use `uv run uncoded` to run the
code in their checkout.

| To…                                   | Use                                     |
| ------------------------------------- | --------------------------------------- |
| Build or refresh the index and skills | `uvx uncoded sync`                      |
| Check generated files without writing | `uvx uncoded check`                     |
| Read a Python symbol's source         | `uvx uncoded body <symbol> --in <file>` |
| Find references to a Python symbol    | `uvx uncoded refs <symbol> --in <file>` |

## `sync`

```sh
uvx uncoded sync
```

Builds or refreshes every configured index and navigation skill. Output lists
files created, updated, or removed. Running it from a subdirectory produces
output at the same project root.

Files that cannot be parsed or decoded are skipped with a warning. Invalid
configuration or roots cause exit status `1`.

## `check`

```sh
uvx uncoded check
```

Runs the same pipeline as `sync` without changing files.

| Status | Meaning                                                                        |
| ------ | ------------------------------------------------------------------------------ |
| `0`    | All generated files match a fresh build.                                       |
| `1`    | A file would be created, updated, or removed, or the configuration is invalid. |

Run `sync` first in a fresh checkout. The local index is not committed.

## `body`

```sh
uvx uncoded body greet --in src/greetings.py
uvx uncoded body Greeter/greet --in src/greetings.py
```

Prints the named symbol's source to standard output, exactly as written in the
file. These examples assume a `greet` function or a `Greeter.greet` method in
`src/greetings.py`.

Use one name for a top-level function, class, module assignment, or Python 3.12
`type` alias. Use `Class/member` for a method or class attribute. Deeper paths
and empty segments are unsupported.

The `--in` path is relative to your current directory, not the configuration
file. No project configuration is required.

## `refs`

```sh
uvx uncoded refs greet --in src/greetings.py
uvx uncoded refs Greeter/greet --in src/greetings.py
```

Finds references to the symbol. Names and `--in` paths follow the same rules as
`body`. Each result is printed as:

```text
path:line:column
```

Positions are one-based. Results are sorted by path and position. Paths within
the current directory are relative; other paths are absolute. Empty output with
exit status `0` means no references were found.

Reference resolution uses the pinned `ty` language server through `uvx`. The
first call may download it. `uvx` must be on `PATH`.

## Lookup errors

`body` and `refs` exit with status `1` if the source cannot be read or parsed,
the symbol is missing, or its name path is unsupported. A reference lookup also
fails if the language server fails. Missing required arguments exit with status
`2`.
