# Stories

This page says what the users of uncoded, the developer and the agent, do with
it, why, and what they see. [The concepts page](concepts.md) says what the words
mean, and [the architecture](architecture.md) says where each thing lives in the
code. This page is an enduring part of the project.

## Why uncoded exists

Agents read code imperfectly in two ways:

- **They miss code that matters to their task.** An agent guesses what to search
  for and searches for it, and it does not find what its guesses did not name.
  That is a failure of recall.
- **They read more code than they need.** Everything an agent reads takes space
  in its context window. That is a failure of precision.

uncoded aims to raise recall by giving the agent the namespace map at the start
of its work. The namespace map lists every symbol under the source roots, so the
agent does not have to guess what exists.

uncoded aims to raise precision by letting the agent read in three steps, each
more detailed than the last, and stop as soon as it knows enough:

1. the namespace map, for every symbol's name and where it is;
2. a stub, for one Python file's imports and the signatures of its symbols;
3. `uncoded body`, for one symbol's definition, exactly as it is in the file.

The documentation index does the same for Markdown. The docs map gives every
heading under the doc roots, and the agent reads only the sections it needs.

That uncoded raises recall and precision is a hypothesis. It has not yet been
tested.

## How uncoded is used

The developer sets uncoded up in a project once. From then on, agents use it,
and the developer rarely runs uncoded themselves. Agents decide when to run
`uncoded sync`. The developer may also set up a pre-commit hook that runs
`uncoded sync`, so that a commit never leaves the installed skill files stale.

Every uncoded command works the same way when run from the project directory or
from any directory beneath it. uncoded is not designed for projects nested
inside one another, each with its own configuration file.

uncoded works the same way on Linux, macOS and Windows. Every path that uncoded
prints, or writes into a generated file, uses `/` to separate directories, on
every system.

Each story describes what happens from the user's point of view, in the order it
happens, using the concepts page's words. It says what the user does and sees,
not how uncoded works inside. The stories come in three groups:

- **Happy paths**, for the developer and then the agent. Each ends with what the
  user gains.
- **User errors**, where the user has done something uncoded cannot accept. Each
  says what the user needs to do.
- **Expected faults**, where something outside uncoded goes wrong.

A bug is behaviour that contradicts a story. That includes a happy path, and
also the handling that a user error or expected fault story promises. A user
error or an expected fault is not itself a bug. Behaviour that a story
explicitly accepts is not a bug, and handling that is better than a story
promises is an enhancement.

## Happy paths

### The developer

#### The developer sets uncoded up in a project

The developer has a Python project, and wants the agents that work in it to find
their way around its code and documentation. In the directory that is to be the
project directory, they run `uvx uncoded init`.

`uncoded init` looks for an existing configuration file in that directory and
the directories above it. Finding none, it writes `.uncoded.toml` in that
directory. In it:

- the source roots are whichever of `src` and `tests` exist in that directory;
- the doc roots are whichever of `README.md`, `AGENTS.md` and `docs` exist in
  that directory.

`uncoded init` then runs `uncoded sync`, which writes the index and the
installed skill files. It ends by doing three things:

- it says which files to commit: the configuration file and the installed skill
  files;
- it prints the lines to add to `AGENTS.md` or `CLAUDE.md`, which tell agents to
  load the navigation skills at the start of every session, one line for each
  kind of root the project has;
- it says that without those lines, agents load the uncoded skills only when
  they choose to.

It exits with status `0`. It does not edit `AGENTS.md`, `CLAUDE.md` or
`pyproject.toml`.

The developer checks the roots in `.uncoded.toml`, and adds the printed lines to
`AGENTS.md` or `CLAUDE.md`. They commit the edited `AGENTS.md` or `CLAUDE.md`,
the configuration file and the installed skill files.

Three variations:

- **None of those directories and files exist.** `uncoded init` writes no
  configuration file. It says which directories and files it looked for, and how
  to write the configuration file by hand. It exits with status `1`. The
  developer writes the file, and runs `uncoded init` again.
- **The project already has a configuration file.** `uncoded init` leaves it as
  it is, says so, and carries on: it runs `uncoded sync`, says which files to
  commit, and prints the lines. Running `uncoded init` a second time therefore
  does no harm.
- **The developer prefers the settings in `pyproject.toml`.** They move the
  settings from `.uncoded.toml` into the `[tool.uncoded]` table of
  `pyproject.toml`, and delete `.uncoded.toml`.

The value to the developer is that setting uncoded up takes one command and one
paste, and that every agent that works in the project from then on is told to
use uncoded.

#### The developer changes what is indexed

The project gains a new package, or the developer wants a directory left out of
the index. The developer edits the roots in the configuration file. The next
`uncoded sync`, run by an agent or by a pre-commit hook, indexes the new roots,
and removes from the index everything that is no longer under any root.

When the developer removes the last source root, that `uncoded sync` also
removes the code index and the installed skill files of the skills that belong
with it, `uncoded-code-navigation` and `uncoded-consistency-review`. Likewise,
when they remove the last doc root, it removes the documentation index and the
installed skill files of `uncoded-doc-navigation`. A project must keep at least
one root. Removing every root is a user error, told under
[A configuration file that names no roots](#a-configuration-file-that-names-no-roots).

The lines in `AGENTS.md` or `CLAUDE.md` load one navigation skill for each kind
of root. When the developer adds the first root of a kind, or removes the last,
they update those lines. Running `uncoded init` again prints the lines for the
roots the project now has.

The developer commits the configuration file, the updated `AGENTS.md` or
`CLAUDE.md`, and any installed skill files that `uncoded sync` changed or
removed.

The value to the developer is that the index follows the configuration file,
with no other step.

#### The developer adds a pre-commit hook

The developer wants a commit to fail when it would leave the installed skill
files stale, for example when an agent forgot to run `uncoded sync`. They add a
hook to their pre-commit configuration that runs `uvx uncoded@<version> sync`,
naming the release of uncoded that the project uses. The hook passes no file
names to the command, and runs on every commit. When the hook changes an
installed skill file, pre-commit fails the commit. Whoever made the commit, the
developer or an agent, stages the changed file and commits again. A CI job that
runs the same pre-commit hooks catches what a local commit missed.

`uncoded check` is for a different need. It reports whether the generated files
are current, without changing anything. It exits with status `0` when they are
current, and with status `1` when they are stale, listing the files that
`uncoded sync` would write or remove. The index is never committed, so in a
fresh checkout, such as CI's, `uncoded check` always reports the index as stale.
It is therefore not a check for CI.

The value to the developer is that stale installed skill files cannot be
committed without anyone noticing.

#### The developer upgrades uncoded

A new release of uncoded is out, and the developer wants it. They raise the
version in the `entry` of their pre-commit hook. At the next commit, the hook
runs the new version, which writes, rewrites or removes the installed skill
files that the new version generates differently. If any change, pre-commit
fails the commit. The developer commits the pre-commit configuration and the
installed skill files together. Before upgrading to a new major version, they
read `docs/upgrading.md`, which says what else to change. That includes deleting
any installed skill files that an earlier version wrote under names the new
version no longer uses, since `uncoded sync` removes only the skills the running
version generates.

Until someone raises the version in the hook, it holds. A new release never
reaches the committed files unannounced. An agent or a developer that runs
another version of uncoded changes only the index, which is local, and the
installed skill files, which the hook writes back at the next commit. A project
without a pre-commit hook pins no version, so each run of `uncoded sync` writes
the installed skill files that its own version generates.

The value to the developer is that upgrading is one deliberate change, visible
in a pull request, and that two projects on one machine can use different
versions of uncoded side by side.

### The agent

#### The agent starts a session

An agent starts work in the project. The lines in `AGENTS.md` or `CLAUDE.md`
tell it to load the navigation skills, and it loads each of them once. Following
them, it runs `uncoded sync` before it reads either map, so that the index is
current, whatever has changed since it was last written. It then reads in full
the namespace map, if the project has source roots, and the docs map, if it has
doc roots.

The value to the agent is that it starts every session from a current index and
a complete list of the project's symbols. That list is what gives it recall.

#### The agent answers a question about the code

The agent needs to understand part of the code. It has the namespace map, so it
does not guess what to search for. It picks the symbols whose names look
relevant, and reads the stubs of the Python files that hold them. A stub shows
the file's imports, each class's bases, and each symbol's signature or
annotation. It leaves out parameter defaults, decorators, docstrings and bodies,
so when the agent needs those, it reads the definition.

For a symbol it is confident it needs, the agent runs
`uncoded body <name path> --in <file>` from the project directory, taking the
name path and the file from the namespace map. It gets the symbol's definition,
exactly as it is in the file, in one call, and the command exits with status
`0`. `uncoded body` prints whole lines, so when another statement shares a line
with the definition, as in `x = 1; y = 2`, it prints that statement too. What
uncoded prints is UTF-8 on every system, whatever encoding the system uses for
its output, so a definition that holds `é` comes out exactly as it is in the
file.

The agent stops as soon as it knows enough, which is often after the namespace
map or a stub.

Some things are not in the namespace map, and the agent reads the file for them:

- a Python file that holds no symbols, which also has no stub;
- a name that is not a symbol: an import, an assignment to more than one target
  or to something other than a bare name, such as `a, b = ...` or
  `self.x = ...`, a name defined inside a function, a class defined inside
  another class, or a name defined inside another statement, such as an `if` or
  a `try`;
- anything that only exists when the code runs, since uncoded reads the code
  without running it.

When the agent is searching for a pattern or a phrase, not for a symbol's name,
it uses a text search such as `grep`, not the index.

The value to the agent is recall from the complete namespace map, and precision
from reading a stub before a definition, and a definition only when it is
needed.

#### The agent answers a question about the documentation

The agent needs to know what the documentation says about a topic. It reads the
docs map, which gives every Markdown file under the doc roots, and each file's
headings, nested by level, with their exact text. The agent picks the heading it
wants, finds it in the file with its own tools, such as `grep` or reading the
file, and reads the section under it.

Two headings with the same text under the same parent heading appear in the docs
map as, for example, "Usage" and "Usage (2)". For "Usage (2)", the agent reads
the section under the second heading called "Usage" under that parent.

The docs map leaves out headings that are underlined, indented, empty, or inside
a fenced code block, and lists a file with no headings without any. For those,
the agent reads the file.

uncoded has no command that prints a section. The agent's own tools find a
heading and read the section under it just as well.

The value to the agent is the same as for code. It sees every heading before it
reads anything, and it reads only the sections it needs.

#### The agent edits a symbol's definition

The agent needs to change a symbol's definition, such as a function's. It runs
`uncoded body` for the symbol, and passes what it prints, unchanged, to its edit
tool as the text to replace. That text is the symbol's definition, exactly as it
is in the file, so the edit lands in the right place without the agent reading
the file to find line numbers.

What `uncoded body` prints is always one unbroken stretch of the file. A
property's definition is its getter, so for a property `uncoded body` prints the
getter. A property's setter or deleter can be elsewhere in the class, so before
changing a property, the agent checks the class for them.

The value to the agent is precision: one call gives exactly the text to change,
and nothing around it.

#### The agent renames a symbol, changes its signature, or deletes it

Before renaming a symbol, changing its signature or deleting it, the agent runs
`uncoded refs <name path> --in <file>` from the project directory. The command
prints every reference to the symbol anywhere in the project directory: its
definition, each import of it, and each use of it. It prints one reference per
line, as `path:line:column`, sorted by path, then line, then column. A path is
relative to the current directory when the reference is beneath it, and absolute
otherwise, so it is relative throughout when the agent runs the command from the
project directory. It exits with status `0`.

The agent updates every reference that the change affects. It deletes a symbol
only when the symbol is unused, as the concepts page defines it.

The value to the agent is recall. It misses no use, no import and no other place
that the change would break.

#### The agent keeps the index current during a task

The index goes stale whenever an indexed file changes, which happens often while
work goes on: the agent edits files, a pull or a checkout changes them, or
another agent or the developer works in the same project. The navigation skills
tell the agent to run `uncoded sync` after it changes an indexed file, and
whenever it sees that something else has changed files, before it relies on the
index again. `uncoded sync` writes only the generated files whose content
changes, removes those the project no longer calls for, such as the stub of a
deleted Python file, lists them all, and exits with status `0`.

The value to the agent is that what it reads in the index is true of the project
as it is.

#### The agent runs the consistency review

The developer asks an agent for a consistency review, or the agent's task calls
for one. The agent loads `uncoded-consistency-review`, runs `uncoded sync`, and
reads the namespace map. It then looks for pairs of claims about the same
concept that ought to agree but do not, such as two names for one thing, or a
docstring that contradicts its function's signature. It reports only the
disagreements it can support, quoting both claims.

The value to the developer is that inconsistencies in the code's names and in
the claims about its symbols are found by a systematic review of the whole code,
not by chance.

## User errors

### Running uncoded outside a project

A user runs an uncoded command other than `uncoded init` in a directory that has
no configuration file, and neither do the directories above it. Often this is an
agent whose shell has moved outside the project. uncoded stops, and says that it
found no configuration file in that directory or above it. It says to run the
command from inside the project, or to set uncoded up with `uncoded init`. It
exits with status `1` and writes nothing.

The user moves to the project directory and runs the command again, or sets
uncoded up.

### A configuration file that cannot be read

The configuration file is not valid TOML, or a setting has the wrong type, such
as `source-roots = "src"` where a list belongs. Every uncoded command that reads
the configuration file stops. uncoded names the file and says what is wrong with
it, in one line. It exits with status `1` and writes nothing.

A `pyproject.toml` on the way up to the configuration file stops every command
in the same way when it is not valid TOML or cannot be read, even when it has no
`[tool.uncoded]` table. uncoded cannot tell whether a file that it cannot read
configures uncoded.

The developer corrects the configuration file.

### A configuration file that names no roots

The configuration file lists no source roots and no doc roots. Usually a setting
is misspelt, and uncoded ignores settings it does not know.

`uncoded sync` and `uncoded check` stop, and so does `uncoded init` when it runs
`uncoded sync`. uncoded says that the configuration file names no roots, and
names the two settings it looks for, `source-roots` and `doc-roots`. It exits
with status `1` and writes nothing. `uncoded body` and `uncoded refs` do not
need roots, and are unaffected.

The developer corrects the setting.

### A root that is missing or the wrong kind

The configuration file names a root that does not exist, or one of the wrong
kind: anything other than a directory as a source root, or anything other than a
directory or a Markdown file as a doc root.

Before writing anything, `uncoded sync` and `uncoded check` examine every root.
uncoded stops, says which root and which setting, and says whether the root is
missing or the wrong kind. It exits with status `1` and writes nothing.

The developer corrects the setting.

### A root outside the project directory

The configuration file names a root outside the project directory, either
directly, or through a symbolic link inside the project that leads out of it.

The same check of every root, before anything is written, finds it. uncoded
stops, says which root and which setting, and says that the root is outside the
project directory. It exits with status `1` and writes nothing.

The developer names a root inside the project directory instead, or moves the
configuration file to a directory that contains the root.

Symbolic links beneath a root are not checked in this way. A linked file beneath
a root is indexed, wherever its target is, and a linked directory beneath a root
is not followed.

### Two configuration files in one directory

One directory holds both `.uncoded.toml` and a `pyproject.toml` with a
`[tool.uncoded]` table, perhaps because the developer moved the settings and
forgot to delete one of them. Every uncoded command, including `uncoded init`,
stops, names both files, and says to keep only one. It exits with status `1` and
writes nothing.

A `pyproject.toml` without a `[tool.uncoded]` table, in the same directory as
`.uncoded.toml`, is not a conflict.

The developer deletes one of the two.

### An `--in` file that cannot be used

An agent gives `uncoded body` or `uncoded refs` an `--in` file that does not
exist, cannot be read, cannot be decoded, cannot be parsed as Python, or is
outside the project directory. uncoded says which file, and which of these is
the problem. It exits with status `1`.

The agent corrects the path. For a file that is not valid Python, it reads the
file by other means.

Any file inside the project directory that parses as Python is accepted, even
one outside the source roots, or one whose name does not end in `.py`, such as a
stub.

### A name path that is malformed or names no symbol

An agent gives a name path with more than two parts, or with an empty part,
where the parts are separated by `/`. Or it gives a name path that names no
symbol in the file. uncoded says either that it accepts only `name` or
`Class/member`, or that the file has no symbol with that name path. It exits
with status `1`.

The agent looks the symbol up in the namespace map and tries again.

### A command used wrongly

A user runs an uncoded command with a missing argument, an argument it does not
take, or an unknown command or option. For example, a pre-commit hook passes
file names to `uncoded sync`, which takes none. uncoded prints how to use the
command, and exits with status `2`. The user corrects the command.

### Editing a generated file by hand

A user edits a generated file, for example to change a skill's wording for their
project, although the file's provenance marker says not to. The next
`uncoded sync` writes the file back as uncoded generates it, and lists it among
the files it updated. Until then, `uncoded check` reports the generated files as
stale.

uncoded has no way to customise its skills. A project that wants different
instructions writes a skill of its own, beside the uncoded skills.

### A file that cannot be read or parsed

A file under a root cannot be used: a Python file that uncoded cannot decode or
parse, often because an agent is part-way through editing it, or a Markdown file
that is not UTF-8. `uncoded sync` warns about each such file, saying why, and
carries on with the rest. It ends with a line saying how many files it skipped.

A skipped file is missing from the index until it can be read and parsed again.
An agent that cannot find a symbol it expected checks the warnings.

`uncoded sync` and `uncoded check` still exit with status `0`. A half-edited
file is normal during a task, and broken Python in a commit is caught by the
tools built for that.

### A name defined twice in one module body or class body

The user's code defines the same name twice in one module body or class body.
That is usually a mistake, although an overloaded function does it on purpose.
The later symbol redefines the earlier one.

The namespace map lists the name once, and the stub shows each definition, in
the order of the file. A name path reaches only the later symbol, so
`uncoded body` prints the later definition. The agent reads the earlier
definition in the stub or the file.

## Expected faults

### `uvx` is missing

`uncoded refs` starts the ty language server through `uvx`, and `uvx` is not on
`PATH`. uncoded says that it could not find `uvx`, and to install uv. It exits
with status `1`.

The developer installs uv. Until then, the agent finds references by searching.

### ty fails

ty cannot be fetched, for example on a first run with no network, or it cannot
start, or it fails. `uncoded refs` stops, says that ty failed, and passes on
what ty or `uvx` said about why. It exits with status `1`. It never reports a
failure of ty as a problem with the `--in` file.

If ty stops responding, `uncoded refs` waits until the agent or the user stops
it. It has no time limit.

The agent tries again later, or finds references by searching.

### A generated file cannot be read, written or removed

`uncoded sync` or `uncoded check` cannot read, write or remove a generated file.
For example, the file lacks permission, the disk is full, or a hand-edited file
is no longer UTF-8. The command stops, says in one line which file and why, and
exits with status `1`. The files `uncoded sync` had already written stay as they
are. Until the cause is fixed and `uncoded sync` runs again, `uncoded check`
reports the generated files as stale.

Two `uncoded sync` runs at once in the same project, for example from two
agents, can meet this fault, when one removes a file the other is about to
remove. uncoded does not prevent it.

The user fixes the cause, and runs `uncoded sync` again.

`uncoded init` stops in the same way when it cannot write the configuration
file. It has written nothing, so the developer fixes the cause and runs
`uncoded init` again.
