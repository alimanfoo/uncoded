# Agent workflow

The generated skills divide navigation into orientation, focused reading, and
reference checks. The index gives the agent the names that exist before it
chooses a file or search term.

## Start a task

An agent loads `.uncoded/namespace.yaml` in full. This map lists directories,
Python files, classes, methods, attributes, functions, and module constants as a
YAML hierarchy.

If the task concerns documentation, the agent also loads `.uncoded/docs.yaml`.
This outline lists every indexed Markdown file and its heading hierarchy.

## Read code

The agent reads a file's matching stub under `.uncoded/stubs/` before it reads
implementation code. A stub records imports, signatures, constants, classes, and
attributes without the bodies.

When the agent needs an implementation, it runs `uncoded body` for that exact
symbol. A symbol name goes through the index and `body`; free text and patterns
still belong in a text search.

## Change code safely

Before renaming, changing a signature, or deleting a symbol, the agent runs
`uncoded refs`. The reference list supplies the complete set of call sites that
must be checked. An empty result supports a dead-symbol check.

After an indexed Python or Markdown change, the agent runs `uncoded sync` before
the next navigation operation. This refresh keeps the namespace, stubs, and
documentation outline aligned with the working tree.

## Review consistency

Repositories with `source-roots` also receive the `uncoded-consistency-review`
skill. It compares concrete claims in symbol names, signatures, docstrings, and
behavior. A finding must quote both conflicting claims and explain why they
describe the same concept. The review excludes general style, complexity,
performance, security, and design advice.

## Know the limits

The namespace and stub extractors use Python's abstract syntax tree. Files that
cannot be parsed or decoded are skipped with a warning. The documentation map
indexes ATX headings that begin with `#`; it does not index Setext headings or
headings inside fenced code blocks.

The index describes static source structure. It does not execute imports,
resolve runtime registration, or replace tests and type checks.
