# Special cases

This page lists every conditional under `src` whose condition names a particular
situation, rather than applies a general rule, with the cause of each. It is the
ledger that [the standard](standard.md)'s "Rules not cases" criterion measures.

A cause should lie outside uncoded, in Python, the operating system or a
protocol that uncoded speaks. A conditional that exists because of a choice
uncoded made is replaced by a general rule instead of being listed. The last
entry on this page is the one exception, as the note under it explains.

Conditionals that apply a general rule are not listed. Examples are the parsing
of CommonMark headings and code fences in `docs_map.py`, the parameter syntax in
`extract.py`, and the rules that the [concepts page](concepts.md) and the
[stories](stories.md) state, such as a doc root that is a Markdown file.

When a change adds a conditional that names a situation, it adds an entry here
in the same pull request. When a change removes one, it removes the entry.

## Python files

| Where                                                 | Situation                                                                         | Cause                                                                                                                                              |
| ----------------------------------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ast_helpers.property_kind`, `class_symbols`          | A method decorated with `@<name>.setter` or `@<name>.deleter` is not a symbol.    | Python's `property` binds a property's setter and deleter to the property's own name, so they belong to the property and are not separate members. |
| `ast_helpers.property_kind`, `extract._extract_class` | A method decorated with `@property` is a property, not a method.                  | Python's `property` turns the method into an attribute that is read, not called.                                                                   |
| `resolver.resolve_name_position`                      | The name of a `def`, `async def` or `class` statement is found after its keyword. | Python's `ast` records the position of the statement, and not of its name.                                                                         |
| `body._definition_text`                               | A decorated function or class starts at its first decorator.                      | Python's `ast` gives a decorated definition the line of its `def` or `class`, not of its first decorator.                                          |
| `stubs._render_class`                                 | A class with no members is rendered with `...` as its body.                       | Python's grammar needs at least one statement in a class body.                                                                                     |

## Processes and files

| Where                        | Situation                                                                          | Cause                                                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `refs._run_ty`               | `uvx` cannot be found, and uncoded says to install uv.                             | The operating system reports a program missing from `PATH` as a missing file.                                                   |
| `refs._terminate`            | Closing ty's input fails, and the failure is ignored.                              | Writing to a pipe fails once the process that reads it has stopped, and ty may stop before it reads every message.              |
| `refs._terminate`            | ty has not stopped 5 seconds after its input closed, and uncoded terminates it.    | A language server stops when its input closes, but uncoded does not control how long ty takes.                                  |
| `refs._read_response`        | A message from ty that does not answer the request is passed over.                 | The Language Server Protocol lets a server send notifications and requests of its own between a request and its response.       |
| `refs._run_exchange`         | ty answers a references request with `null`, which uncoded reads as no references. | The Language Server Protocol allows `null` as the result of a references request.                                               |
| `sync._remove_empty_parents` | A symbolic link to a directory stops the removal of empty directories.             | `rmdir` fails on a symbolic link on Linux and macOS, and on Windows it removes the link, which the developer made, not uncoded. |
| `cli._report_lookup_error`   | An `--in` file that does not exist gets its own message.                           | uncoded chose its own wording for a missing file. See the note below.                                                           |

The last entry's cause is a choice uncoded made, the wording of one message,
where a general rule exists: `read_helpers.failure_reason` gives the reason a
file could not be read without naming it again, and `uncoded sync` already uses
it. Applying it to `uncoded body` and `uncoded refs` would change the messages
they print, which is the product owner's decision.
