# Ontology

This document names the things uncoded deals with and says what the words mean,
while [the architecture](architecture.md) says where each thing lives in the
code.

The ontology is an enduring part of the project. Changes to the code, the
documentation, the skills and the specifications should keep these meanings, or
update this document deliberately.

The product's name is uncoded, in lower case even at the start of a sentence.

Each term has its own entry, which uses only terms explained before it. An entry
ends with the words the term replaces. Those words are not used for the concept,
in code, documents, skills or issues. Where the code, documents or skills
disagree with this document, they are wrong and are corrected to match it.

The dated specifications record the design of particular pieces of work. Where
their words conflict with this document, this document is authoritative.

## Terms

### Project

A **project** is a codebase that uses uncoded.

Replaces: "host project".

### Configuration file

A project's **configuration file** is where its uncoded settings live: either a
`.uncoded.toml` file, with the settings as top-level keys, or a `pyproject.toml`
file, with the settings in its `[tool.uncoded]` table.

Replaces: "config file".

### Project directory

A project's **project directory** is the directory that holds its configuration
file.

It is not necessarily the top of a Git repository. A subproject in a monorepo
can have its own project directory, and a project need not use Git at all.

Replaces: "project root", "repository root".

### Python file

A **Python file** is a file whose name ends in `.py`. Python calls the code in
one a module, and the statements directly in it, not nested in another
statement, its module body.

### Symbol

A **symbol** is a named thing that uncoded indexes in a Python file. In the
module body it is a class, a function, a `type` statement, or an assignment or
annotation whose one target is a bare name, such as `x = 1` or `x: int`.
Directly in a class body it is a method, a property, or such an assignment or
annotation. A property is a method decorated with `@property`, which uncoded
treats as a property and not as a method.

Each symbol has a name and one definition. Two symbols can share a name, such as
two functions called `parse` in different Python files. Directories and files
are not symbols, and neither are names defined inside a function, inside a
nested class, or inside another statement such as `if` or `try`. This is
narrower than Python's own sense, in which imports and other bindings also name
symbols.

Replaces: "module constant", which is an assignment at module level.

### Definition

A symbol's **definition** is the statement that defines it: a class or function
definition, from its first decorator to the end of its body, or an assignment or
`type` statement. A property's definition also includes its setter and deleter,
which are not symbols of their own.

`uncoded body` prints a symbol's definition, except that for a property it
prints only the getter.

Replaces: "body" and "source body" for a whole definition. In Python's grammar a
body is only the suite after the definition's colon.

### Name path

A **name path** identifies a symbol within one Python file. For a symbol at
module level, it is the symbol's name, as `greet`. For a symbol in a class body,
it is the class's name, a slash and the symbol's name, as `Greeter/greet`.

`uncoded body` and `uncoded refs` take a name path to say which symbol they
mean. Serena, an LSP-based toolkit for agents, uses the same term.

Replaces: "symbol path".

### Shadowing

A symbol **shadows** another when it has the same name and is defined later in
the same module body or class body. A name path refers to the later symbol, and
the earlier one cannot be named, as in Python, where the later binding replaces
the earlier. A bare annotation such as `x: int` binds nothing, but is treated
the same way.

Shadowing is rare, and usually a mistake. An overloaded function is the common
exception: each `@overload` definition is shadowed by the next, and the last
definition, usually the implementation, is the symbol.

### Reference

A **reference** is a place in Python source where a symbol's name stands for
that symbol, and not for another symbol with the same name: where the symbol is
defined, imported or used.

`uncoded refs` finds a symbol's references through the ty language server, and
prints each as `path:line:column`.

### Heading

A **heading** is one of a subset of CommonMark's ATX headings: a line that
starts in its first column with one to six `#` characters and a space, followed
by non-empty text, outside a fenced code block. uncoded does not index setext
headings, which are underlined.

### Root

A **root** is a directory or file at the top of a part of a project that uncoded
indexes. The `source-roots` and `doc-roots` settings list a project's roots.

Replaces: "root type", for whether a root is a source root or a doc root.

### Source root

A **source root** is a directory listed in the `source-roots` setting. uncoded
indexes the symbols in every Python file beneath it, at any depth.

### Doc root

A **doc root** is a directory or a Markdown file listed in the `doc-roots`
setting. uncoded indexes the headings in that file, or in every Markdown file
beneath that directory, at any depth. A Markdown file is a file whose name ends
in `.md`. A single file can be a root because its headings form a tree of their
own.

### Namespace map

The **namespace map** is the file `.uncoded/namespace.yaml`. It holds the
symbols of the Python files under the source roots as one tree: directories and
files by their path relative to the project directory, each file's symbols
beneath it, and each class's symbols beneath the class. A file with no symbols
is left out.

### Docs map

The **docs map** is the file `.uncoded/docs.yaml`. It holds the headings of the
Markdown files under the doc roots as one tree: directories and files by their
path relative to the project directory, and each file's headings beneath it,
nested by level. A file with no headings is listed without any.

Replaces: "doc map", "heading map", "heading outline".

### Stub

A **stub** is a `.pyi` file in Python's stub syntax that uncoded writes, for
agents to read, for one Python file that has symbols. It holds the file's
imports from its module body, each class's bases, each function's and method's
signature, and each assignment's annotation and, when short, its value. It sits
at the Python file's path relative to the project directory, under
`.uncoded/stubs/`.

A stub is not a type stub for type checkers. It leaves out parameter defaults
and decorators, so a type checker would misread it.

### Code index

The **code index** is the namespace map and the stubs.

Replaces: "symbol index".

### Documentation index

The **documentation index** is the docs map.

### Index

The **index** is the code index and the documentation index together. All its
files are under `.uncoded/`.

### Agent

An **agent** is an AI coding agent working in a project, such as one running in
Claude Code or Codex.

Replaces: "coding agent" and "AI coding agent", except to introduce the term.

### Skill

A **skill** is a named set of instructions that uncoded generates for an agent
to load when its task calls for them.

### uncoded skills

The **uncoded skills** are the three skills uncoded generates:
`uncoded-code-navigation`, `uncoded-doc-navigation` and
`uncoded-consistency-review`.

### Navigation skills

The **navigation skills** are `uncoded-code-navigation` and
`uncoded-doc-navigation`.

### Skill source

A **skill source** is the Markdown file in uncoded's package that holds the text
of a skill. uncoded adds the skill's name and description when it generates the
skill.

Replaces: "package resource", and "skill instructions" or "source" for a skill
source.

### Installed skill file

An **installed skill file** is a skill's `SKILL.md`, placed in a project where
agents look for skills.

uncoded writes each skill to `.claude/skills/<name>/SKILL.md` for Claude Code
and to `.agents/skills/<name>/SKILL.md` for Codex.

### Consistency review

The **consistency review** is the review an agent carries out by following
`uncoded-consistency-review`. It reports disagreements between two claims about
the same concept, with verbatim evidence for each.

### Generated file

A **generated file** is a file that uncoded writes in a project: one of the
index's files, an installed skill file, or `.uncoded/.gitignore`.

`uncoded sync` writes the generated files, and removes any that uncoded no
longer generates.

Replaces: "artefact", "index artefact", "navigation artefact".

### Provenance marker

The **provenance marker** is the text "Generated by uncoded — do not edit;
regeneration overwrites." Every generated file carries it in a comment. The code
defines it once, as `GENERATED_MARKER`.

### Current

A project's generated files are **current** when they are exactly what uncoded
would generate from the project as it is now: none missing, none left over, and
none with different content. The index is current when its files are.

`uncoded check` reports whether the generated files are current, without writing
any.

Replaces: "up to date", "matches a fresh build".

### Stale

A project's generated files are **stale** when they are not current. The index
is stale when its files are.

### Developer

A **developer** is a person who sets up uncoded in a project.

A developer writes the configuration file and commits the installed skill files.
`uncoded sync` and `uncoded check` are run for them, by agents or by tools they
set up, such as a pre-commit hook of their own.

Replaces: "user", "contributor".

## Relationships and rules

This section says how the things above relate. What uncoded does with them, and
when, is for the stories.

### The project directory

Every root, every Python file uncoded is asked about, and every generated file
sits inside the project directory.

### The index

The code index is built from the source roots, and the documentation index from
the doc roots. Neither depends on the other.

Each uncoded skill belongs with one part of the index. `uncoded-code-navigation`
and `uncoded-consistency-review` belong with the code index, and
`uncoded-doc-navigation` with the documentation index.

`.uncoded/.gitignore` keeps the index out of Git: it ignores everything under
`.uncoded/`, itself included. The installed skill files are meant to be
committed with the project.

### Symbols and references

A symbol's references include its definition, so every symbol has at least one.
A symbol is unused when every reference to it lies within its own definition.

References within the definition of a symbol that it shadows are not uses
either. An unused overloaded function therefore has a reference in each
`@overload` definition, and is still unused.
