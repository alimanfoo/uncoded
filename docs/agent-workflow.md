# Agent workflow

The generated skills tell your agent when to load the index, read source, and
check references. Once you have [set up the repository](getting-started.md), the
agent follows this workflow during a coding task.

## Start a task

The agent loads `.uncoded/namespace.yaml` in full to learn the Python symbols
that exist. For a documentation task, it loads `.uncoded/docs.yaml` to find the
relevant file and heading.

Navigation skills load once per session. Their instructions apply throughout the
session.

## Read code

The agent adds detail only when the task needs it. This progressive disclosure
keeps broad work on compact views and limits source reads to the implementations
that matter.

1. The namespace map shows every indexed symbol and its file. It is often enough
   for questions about structure or where a feature lives.
2. The file's stub under `.uncoded/stubs/` adds imports, signatures, constants,
   and attributes. It is often enough for questions about interfaces and types.
3. `uncoded body` returns one symbol's exact source when the task needs it:

```sh
uvx uncoded body greet --in src/greetings.py
```

This example assumes `greet` is defined in `src/greetings.py`. For a method, use
`ClassName/method_name`. See [the command reference](commands.md#body) for
supported symbols and paths.

A file with no indexed symbols has no stub, so the agent reads the file
directly. Free text and patterns still belong in a text search.

## Change a symbol

Before renaming, changing a signature, or deleting a symbol, the agent checks
its references:

```sh
uvx uncoded refs greet --in src/greetings.py
```

The results identify the sites to inspect and update. After changing indexed
Python or Markdown files, the agent runs `uncoded sync` before navigating again.

## Review consistency

With `source-roots` configured, uncoded also generates a consistency review
skill. It looks for concrete disagreements between names, signatures,
docstrings, and behavior. Every finding must quote both conflicting claims and
show that they describe the same concept.

Invoke it with `$uncoded-consistency-review` in Codex or
`/uncoded-consistency-review` in Claude Code.

## Know the limits

The code index describes static Python structure. It does not run imports or
resolve runtime registration. Files that cannot be parsed or decoded are skipped
with a warning.

The documentation index records headings that begin with `#`. It excludes
underlined headings and headings inside fenced code blocks. Read documentation
sections directly; `body` and `refs` operate on Python symbols.

Keep using tests and type checks to verify changes.
