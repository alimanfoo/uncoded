# Ontology

This document names the things uncoded deals with and says what the words mean,
while [the architecture](architecture.md) says where each thing lives in the
code.

The ontology is an enduring part of the project. Changes to the code, the
documentation, the skills and the specifications should keep these meanings, or
update this document deliberately.

The product's name is uncoded, in lower case even at the start of a sentence.

Each term has its own definition, and uses only terms defined before it. A
definition ends with the words the term replaces. Those words are not used for
the concept, in code, documents, skills or issues.

The dated specifications record the design of particular pieces of work. Where
their words conflict with this document, this document is authoritative.

## Definitions

### Project

A **project** is the codebase uncoded is configured in.

Replaces: "host project".

### Configuration file

The **configuration file** is the `pyproject.toml` or `.uncoded.toml` that
configures uncoded for a project.

Replaces: "config file".

### Project directory

A project's **project directory** is the directory that holds its configuration
file. It is not necessarily the top of a Git repository: a subproject in a
monorepo can have its own project directory, and a project need not be in Git at
all.

Replaces: "project root", "repository root".

### Symbol

A **symbol** is a class, function, method, module-level assignment, class
attribute or `type` alias in Python source. Each symbol has a name and a
definition. Two symbols can share a name, such as two functions called `parse`
in different modules. Directories and files are not symbols.

Replaces: "module constant", which is a module-level assignment.

### Definition

A symbol's **definition** is the code that defines it, as Python's grammar has
it. For a function or class, it runs from its first decorator to the end of its
body.

`uncoded body` prints a symbol's definition.

Replaces: "body" and "source body" for the whole definition. In Python's grammar
a body is only the indented block.

### Name path

A **name path** identifies a symbol within one Python file. For a symbol defined
at module level, it is the symbol's name, as `greet`. For a method or class
attribute, it is the class's name, a slash, and the symbol's name, as
`Greeter/greet`.

`uncoded body` and `uncoded refs` take a name path to say which symbol they
mean. The term is the one LSP-based tools such as Serena use.

Replaces: "symbol path".

### Reference

A **reference** is a place in Python source where a symbol's name stands for
that symbol, and not for another symbol with the same name. It is where the
symbol is defined, imported or used.

`uncoded refs` prints each reference as `path:line:column`. These are the
references a language server returns when asked to include the declaration.

### Root

A **root** is where uncoded starts building a tree.

Replaces: "root type", which is "source roots" or "doc roots".

### Source root

A **source root** is a directory listed in `source-roots`. uncoded builds a tree
of directories, files and symbols from it.

### Doc root

A **doc root** is a directory or a single Markdown file listed in `doc-roots`.
uncoded builds a tree of headings from it. A single file is a root because its
headings form a tree.

### Namespace map

The **namespace map** is the file `.uncoded/namespace.yaml`. It lists every
directory, file and symbol under the source roots as one tree.

### Stub

A **stub** is the file at a Python file's path under `.uncoded/stubs/`, with a
`.pyi` suffix. It holds the Python file's imports and each symbol's signature or
annotation, without bodies.

### Docs map

The **docs map** is the file `.uncoded/docs.yaml`. It lists every Markdown file
under the doc roots and nests each file's headings as a tree.

Replaces: "doc map", "heading map", "heading outline".

### Code index

The **code index** is the namespace map and the stubs.

Replaces: "symbol index".

### Documentation index

The **documentation index** is the docs map.

### Index

The **index** is the code index and the documentation index together: every file
uncoded generates under `.uncoded/` for navigating a project.

### Agent

An **agent** is an AI coding agent working in a project, such as Claude Code or
Codex.

Replaces: "coding agent" and "AI coding agent", except to introduce the term.

### Skill

A **skill** is a set of instructions uncoded generates for an agent to load.

### uncoded skills

The **uncoded skills** are the three skills uncoded generates:
`uncoded-code-navigation`, `uncoded-doc-navigation` and
`uncoded-consistency-review`.

### Navigation skills

The **navigation skills** are `uncoded-code-navigation` and
`uncoded-doc-navigation`.

### Skill source

A **skill source** is the Markdown file in uncoded's package that a skill is
rendered from.

Replaces: "package resource", "skill instructions", and "source" for a skill
source.

### Installed skill file

An **installed skill file** is a skill's `SKILL.md` in a project.

### Consistency review

The **consistency review** is the review that `uncoded-consistency-review`
carries out. It reports disagreements between two claims about one concept, with
the evidence for each.

### Generated file

A **generated file** is any file uncoded generates in a project: the index's
files, the installed skill files and `.uncoded/.gitignore`.

`uncoded sync` writes the generated files.

Replaces: "artefact", "index artefact", "navigation artefact".

### Provenance marker

The **provenance marker** is the line that says a file was generated by uncoded
and must not be edited. Every generated file carries it. The code defines it
once, as `GENERATED_MARKER`.

### Current

A generated file is **current** when it matches what uncoded would generate from
the project as it is now. The index is current when all its files are.

`uncoded check` reports whether every generated file is current, without writing
any.

Replaces: "up to date", "matches a fresh build".

### Stale

A generated file is **stale** when it is not current. The index is stale when
any of its files is.

### Developer

A **developer** is the person who sets up uncoded in a project.

A developer writes the configuration file, runs `uncoded sync` and
`uncoded check`, and commits the installed skill files. The documentation
addresses them as "you".

Replaces: "user", "contributor".

## Relationships and rules

This section says how the things above relate. What uncoded does with them, and
when, is for the user stories.

### The project directory

Everything uncoded reads or writes sits inside the project directory: its roots,
any Python file it is asked about, and its generated files.

### The index

The code index is built from the source roots, and the documentation index from
the doc roots. Neither depends on the other.

Each uncoded skill belongs with one part of the index. The code navigation skill
and the consistency review belong with the code index, and the doc navigation
skill with the documentation index.

The installed skill files are part of the project, in its version control. The
index is not: it is local to each checkout.

### Symbols and references

A symbol's references are where it is defined, imported and used, so every
symbol has at least one. A symbol is unused when every reference to it is part
of its own definition. An unused property with a setter, or an unused function
with overloads, has more than one such reference.
