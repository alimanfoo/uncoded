# Special cases

This page lists every conditional under `src` whose condition names a particular
situation, rather than applies a general rule, with the cause of each. It is the
ledger that [the standard](standard.md)'s "Rules not cases" criterion measures,
and the standard sets the bar for each entry's cause.

Conditionals that apply a general rule are not listed. Examples are the choice
of ATX headings in `docs_map.py`, the parameter syntax in `extract.py`, and the
rules that the [concepts page](concepts.md) and the [stories](stories.md) state,
such as a doc root that is a Markdown file.

## Python files

| Where                                                  | Situation                                                                                        | Cause                                                                                                                                              |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ast_helpers.property_kind`, `class_symbols`           | A method decorated with `@<name>.setter` or `@<name>.deleter` is not a symbol.                   | Python's `property` binds a property's setter and deleter to the property's own name, so they belong to the property and are not separate members. |
| `ast_helpers.property_kind`, `extract._extract_member` | A method decorated with `@property` is a property, not a method.                                 | Python's `property` turns the method into an attribute that is read, not called.                                                                   |
| `resolver.resolve_name_position`                       | The name of a `def`, `async def` or `class` statement is the first name token after its keyword. | Python's `ast` records the position of the statement, and not of its name.                                                                         |
| `body._definition_text`                                | A decorated function or class starts at its first decorator.                                     | Python's `ast` gives a decorated definition the line of its `def` or `class`, not of its first decorator.                                          |
| `read_helpers.failure_reason`                          | A `SyntaxError` from an invalid encoding cookie has no filename but embeds it in its message.    | CPython formats the error as `unknown encoding for '<path>': <codec>`, so the path must be removed from the reason.                                |
| `stubs._render_class`                                  | A class with no members is rendered with `...` as its body.                                      | Python's grammar needs at least one statement in a class body.                                                                                     |
| `stubs._symbol_blocks`                                 | A `type` statement shares a block with assignments.                                              | ruff, whose layout the standard stub style is, writes no blank line between consecutive simple statements, and both are simple statements.         |

## Processes and files

| Where                        | Situation                                                                          | Cause                                                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `refs._run_ty`               | `uvx` cannot be found, and uncoded says to install uv.                             | The operating system reports a program missing from `PATH` as a missing file.                                                   |
| `refs._terminate`            | Closing ty's input fails, and the failure is ignored.                              | Writing to a pipe fails once the process that reads it has stopped, and ty may stop before it reads every message.              |
| `refs._terminate`            | ty has not stopped 5 seconds after its input closed, and uncoded terminates it.    | A language server stops when its input closes, but uncoded does not control how long ty takes.                                  |
| `refs._read_response`        | A message from ty that does not answer the request is passed over.                 | The Language Server Protocol lets a server send notifications and requests of its own between a request and its response.       |
| `refs._run_exchange`         | ty answers a references request with `null`, which uncoded reads as no references. | The Language Server Protocol allows `null` as the result of a references request.                                               |
| `sync._remove_empty_parents` | A symbolic link to a directory stops the removal of empty directories.             | `rmdir` fails on a symbolic link on Linux and macOS, and on Windows it removes the link, which the developer made, not uncoded. |
