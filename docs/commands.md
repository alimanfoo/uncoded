# Commands

Run uncoded with `uvx uncoded`. Contributors use `uv run uncoded` to run the
code in their checkout.

| To…                                   | Use                                     |
| ------------------------------------- | --------------------------------------- |
| Set uncoded up in a project           | `uvx uncoded init`                      |
| Build or refresh the index and skills | `uvx uncoded sync`                      |
| Check generated files without writing | `uvx uncoded check`                     |
| Read a Python symbol's source         | `uvx uncoded body <symbol> --in <file>` |
| Find references to a Python symbol    | `uvx uncoded refs <symbol> --in <file>` |
| Print the installed version           | `uvx uncoded --version`                 |

Every command but `init` and `--version` runs inside a project. It finds the
configuration file in the current directory or the nearest directory above it.
If there is none, it exits with status `1`.

## `init`

```sh
uvx uncoded init
```

Sets uncoded up in the project, then runs `sync`. Run it in the directory that
is to be the project directory.

If no configuration file is found in that directory or above it, `init` writes
`.uncoded.toml` there. Its source roots are whichever of `src` and `tests`
exist, its doc roots are whichever of `README.md`, `AGENTS.md` and `docs` exist,
and its required version is the version of uncoded that is running. If none of
them exist, `init` writes nothing and exits with status `1`. A configuration
file that `init` finds is left as it is.

If `sync` fails, `init` stops there with exit status `1`. After `sync`, `init`
says which files to commit, and prints the lines to add to `AGENTS.md` or
`CLAUDE.md` that tell agents to load the navigation skills. It does not edit
those files or `pyproject.toml`. Running it again does no harm.

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

The index is never committed, so in a fresh checkout `check` always reports it
as stale. It is not a check for CI. See
[Keep the index current](keeping-current.md#check-without-writing).

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
file. It must be inside the project directory, once symbolic links are resolved.
Run `body` from the project directory, where the namespace map's paths work as
`--in` paths as given.

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
the current directory are relative; other paths are absolute. Every path uses
`/` to separate directories, on Windows too. Empty output with exit status `0`
means no references were found.

Reference resolution uses the pinned `ty` language server through `uvx`. The
first call may download it. `uvx` must be on `PATH`.

## `--version`

```sh
uvx uncoded --version
```

Prints `uncoded` and the installed version, such as `uncoded 3.0.1`.

## Lookup errors

`body` and `refs` exit with status `1` if the `--in` file is outside the project
directory, the source cannot be read or parsed, the symbol is missing, or its
name path is unsupported. A reference lookup also fails if the language server
fails. Missing required arguments exit with status `2`.
