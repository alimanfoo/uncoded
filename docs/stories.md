# Stories

This page says what the users of uncoded do with it, why, and what they see,
while [the concepts page](concepts.md) says what the words mean and
[the architecture](architecture.md) says where each thing lives in the code. It
is an enduring part of the project.

## Why uncoded exists

Agents read code imperfectly in two ways. They sometimes fail to find code that
matters to their task: they guess what to search for, grep for it, and miss what
their guesses did not name. That is a failure of recall. They also read more
code than they need, which spends context. That is a failure of precision.

uncoded aims to raise recall by giving an agent the complete namespace map at
the start of its work, so that it knows every symbol in the project without
guessing. It aims to raise precision by progressive disclosure: the agent reads
the namespace map, then the stub of a Python file whose symbols look relevant,
and only then, for a symbol it is confident it needs, the symbol's definition,
exactly and completely, with `uncoded body`. The documentation index does the
same for Markdown headings.

That uncoded raises recall and precision is a hypothesis. It has not yet been
tested.

## How uncoded is used

A developer sets uncoded up in a project once. From then on, agents use it, and
the developer rarely runs uncoded by hand. Agents decide when the index needs
`uncoded sync`. Tools the developer sets up, such as a pre-commit hook or CI,
may run `uncoded sync` or `uncoded check` as a backstop.

uncoded behaves the same on Linux, macOS and Windows. Every path it prints or
writes uses `/`, on every system.

Each story is told from the user's seat, in the order things happen, in the
concepts page's words, citing no mechanism. The happy paths come first, for the
developer and then for the agent, and each says what the user gains. Then come
the user errors, each saying what the user needs to do, and then the expected
faults.

A bug is behaviour that contradicts a story, whether a happy path or the
handling that a user error or expected fault story promises. A user error is
something the user did, and an expected fault is something outside uncoded going
wrong. Neither cause is itself a bug. Behaviour a story explicitly accepts is
not a bug, and better handling than a story promises is an enhancement.

## Happy paths

### The developer

#### The developer sets uncoded up in a project

The developer has a Python project and wants the agents that work in it to find
their way around its code and documentation. In the directory that is to be the
project directory, they run `uvx uncoded init`.

`uncoded init` looks for an existing configuration file, from that directory
upwards. Finding none, it writes `.uncoded.toml` in that directory. The file
names as source roots whichever of `src` and `tests` exist, and as doc roots
whichever of `README.md`, `AGENTS.md` and `docs` exist. It sets the required
version to the version of uncoded that is running. `uncoded init` never edits
`pyproject.toml`. A developer who prefers the settings in `pyproject.toml` moves
them into its `[tool.uncoded]` table.

`uncoded init` then runs `uncoded sync`, which writes the index and the
installed skill files. It ends by saying what to commit, the configuration file
and the installed skill files, and it prints the lines to add to `AGENTS.md` or
`CLAUDE.md`, which tell agents to load the navigation skills at the start of a
session. It says that without those lines, agents load the uncoded skills only
when they choose to. It edits neither file itself. It exits with status `0`.

The developer checks the roots in the configuration file, adds the printed
lines, and commits. If the project already had a configuration file,
`uncoded init` leaves it as it is and says so, and carries on. Running
`uncoded init` again does no harm.

The value to the developer is that setting uncoded up is one command and one
paste, and every agent that works in the project from then on uses it.

#### The developer changes what is indexed

The project grows a new package, or the developer wants a directory left out.
They edit the roots in the configuration file. The next `uncoded sync`, run by
an agent or a tool, indexes the new roots and removes from the index everything
that came only from roots no longer listed. When the last source root goes, the
code index and the skills that belong with it go too, and likewise for the doc
roots and the documentation index. The developer commits the configuration file
and any installed skill files that changed.

The value is that the index follows the configuration with no other step.

#### The developer adds a backstop

The developer wants to know when the committed installed skill files no longer
match what uncoded generates. They add a pre-commit hook of their own that runs
`uncoded sync`, or a CI step that runs `uncoded check`, at the project's
required version. `uncoded check` writes nothing. It exits with status `0` when
the generated files are current, and with status `1` when they are stale,
listing what would change.

The value is that a forgotten `uncoded sync` is caught before it lands, without
anyone remembering to look.

#### The developer upgrades uncoded

A new release of uncoded is out, and the developer wants it. They raise the
required version in the configuration file. The next `uncoded sync` at the new
version rewrites any generated files that the new version writes differently.
The developer commits the configuration file and the installed skill files
together. After a major release, they first read the upgrading guide for what
else to change.

Until someone raises it, the required version holds. A new release never reaches
a project unannounced, and every machine, agent and tool runs the same version.

The value is that upgrading is one deliberate change that shows in a pull
request, and two projects on one machine can use different versions side by
side.

### The agent

#### The agent starts a session

An agent starts work in the project, and the instructions in `AGENTS.md` or
`CLAUDE.md` tell it to load the navigation skills. It loads them once. Following
them, it runs `uncoded sync` before anything else, so that the index reflects
the project as it is now, whatever has changed since the index was last written.
The agent then reads the namespace map, and the docs map when its task concerns
documentation.

If the agent runs uncoded at a version other than the required version, uncoded
refuses and gives the command for the right one, and the agent uses that command
from then on.

The value to the agent is that it starts every session from a current index and
a complete view of the project's symbols, which is where its recall comes from.

#### The agent answers a question about the code

The agent needs to understand some part of the code. It has the namespace map,
so it does not guess what to search for. It picks the symbols whose names look
relevant and reads the stubs of their Python files, which show their signatures,
the classes they belong to and the imports that connect them. For a symbol it is
confident it needs, it runs `uncoded body <name path> --in <file>` from the
project directory, taking the name path and file from the namespace map, and
gets the symbol's definition, exactly as it is in the file and in one call, with
exit status `0`. It stops as soon as it knows enough, which is often at the
namespace map or a stub.

A Python file with no symbols has no stub, and the agent reads it directly. A
name defined inside a function, a nested class or another statement such as an
`if` or a `try` is not a symbol, so the agent finds it by reading the file.

The value is recall from the complete namespace map, and precision from reading
the stub before the definition, and the definition only when it is needed.

#### The agent answers a question about the documentation

The agent needs to know what the documentation says about a topic. It reads the
docs map, which gives every Markdown file under the doc roots and each heading's
exact text. It finds the heading it wants in the file with its own tools, such
as `grep` or reading the file, and reads the section beneath it. When a heading
repeats at the same level, the docs map writes it with " (2)", " (3)" and so on,
and the agent searches for the heading's text and takes that occurrence.

uncoded has no command to print a section. The agent's own tools find a section
from its heading as easily, so none is needed.

The value is the same as for code: the agent sees every heading before it reads
anything, and reads only the sections it needs.

#### The agent edits a symbol's definition

The agent needs to change a function or a class. It runs `uncoded body` for the
symbol, and passes what it prints, unchanged, to its edit tool as the text to
replace. That text is the symbol's whole definition exactly as it is in the
file, so the edit lands where it should without the agent reading the file to
work out line numbers.

The value is precision: one call gives exactly the text to change, and nothing
around it.

#### The agent renames a symbol, changes its signature, or deletes it

Before changing anything that other code depends on, the agent runs
`uncoded refs <name path> --in <file>` from the project directory. It prints
every reference to the symbol, one per line as `path:line:column`, sorted by
path and position: the symbol's definition, each import of it and each use of
it, anywhere in the project, and exits with status `0`. The agent visits each
one. It deletes a symbol only when every reference lies within its own
definition.

The value is recall: the agent misses no caller, no import and no other place
that would break.

#### The agent keeps the index current during a task

The index goes stale whenever files change, for many reasons while work goes on:
the agent's own edits, a pull or a checkout, or another agent or the developer
working in the same project. The navigation skills tell the agent to run
`uncoded sync` after it changes indexed files, and whenever it notices that
files have changed under it, before it relies on the index again. `uncoded sync`
writes only the generated files that have changed, lists them, and exits with
status `0`.

The value is that what the agent reads in the index is true of the project.

#### The agent runs the consistency review

The developer asks the agent for a consistency review, or the agent's task calls
for one. The agent loads `uncoded-consistency-review`, runs `uncoded sync`,
reads the namespace map, and looks for two claims about the same concept that
ought to agree but do not, such as two names for one thing or a docstring that
contradicts a signature. It reports only disagreements it can support, quoting
both claims.

The value is that inconsistencies in vocabulary and contracts are found by
reading the whole project, not by chance.

## User errors

### Running uncoded outside a project

A user runs an uncoded command in a directory with no configuration file in it
or above it, often an agent whose shell has moved outside the project. uncoded
stops, says that it found no configuration file from that directory upwards, and
says to run `uncoded init` in the project directory or to run the command from
inside a project. It exits with status `1` and writes nothing. The user moves to
the project directory, or sets uncoded up.

### A configuration file that names no roots

The developer's configuration file names no roots, usually through a misspelt
setting, since uncoded ignores settings it does not know. uncoded stops, says
that the configuration file names no roots, and names the two settings it looks
for, `source-roots` and `doc-roots`. It exits with status `1` and writes
nothing. The developer corrects the setting.

### A root that is missing or the wrong kind

The developer names a root that does not exist, or one of the wrong kind: a file
as a source root, or anything but a directory or a Markdown file as a doc root.
uncoded checks every root before it writes anything. It stops, says which root
and which setting, and whether the root is missing or the wrong kind. It exits
with status `1` and writes nothing. The developer corrects the setting.

### A root outside the project directory

The developer names a root outside the project directory, directly or through a
symbolic link that leads out. The same check, made before anything is written,
stops uncoded, and it says which root and which setting, and that the root is
outside the project directory. It exits with status `1` and writes nothing. The
developer moves the root into the project, or moves the configuration file to a
directory that contains it.

### Two configuration files in one directory

The developer has uncoded settings in both `.uncoded.toml` and the
`[tool.uncoded]` table of `pyproject.toml` in the same directory, perhaps after
moving them and forgetting to delete one. Every command stops, `uncoded init`
included, names both files, and says to keep one. It exits with status `1` and
writes nothing. A `pyproject.toml` with no `[tool.uncoded]` table beside an
`.uncoded.toml` is not a conflict.

### Running a version other than the required version

An agent or a tool runs a version of uncoded other than the project's required
version. uncoded stops before doing anything, says which version the project
needs, and gives the command to run it, `uvx uncoded@<version> <command>`. It
exits with status `1` and writes nothing. The agent runs the command again at
that version.

### An `--in` file that cannot be used

An agent gives `uncoded body` or `uncoded refs` an `--in` file that does not
exist, cannot be read or decoded, cannot be parsed as Python, or lies outside
the project directory. uncoded says which file, and which of these is wrong. It
exits with status `1`. The agent corrects the path, or reads a file that is not
valid Python by other means. A Python file inside the project directory but
outside the source roots is accepted.

### A name path that is malformed or names no symbol

An agent gives a name path with more than two parts or an empty part, or one
that names no symbol in the file. uncoded says that it accepts only `name` or
`Class/member`, or that the file has no symbol with that name path. It exits
with status `1`. The agent looks the symbol up in the namespace map and tries
again.

### Editing a generated file by hand

A user edits a generated file, perhaps to change a skill's wording for their
project, despite the provenance marker. The next `uncoded sync` puts the file
back as uncoded generates it and lists it among the files it updated. Until
then, `uncoded check` reports the generated files as stale. uncoded has no way
to customise its skills. A project that wants different instructions writes a
skill of its own alongside them.

### A file that cannot be read or parsed

A file under a root cannot be read or parsed: a Python file uncoded cannot
decode or parse, often one an agent is half-way through editing, or a Markdown
file that is not UTF-8. `uncoded sync` warns about each such file, saying why,
carries on with the rest, and ends with a line saying how many files it skipped.
The file is absent from the index until it can be parsed again, so an agent that
cannot find a symbol it expected checks the warnings. `uncoded sync` and
`uncoded check` still exit with status `0`: a half-edited file is normal during
a task, and broken Python in a commit is caught by the tools built for that.

### A name defined twice in one module or class body

The user's code defines a name twice in one module body or class body. That is
usually a mistake, though an overloaded function does it on purpose. The later
symbol redefines the earlier one. The namespace map lists the name once, and the
stub shows each definition. A name path reaches only the later symbol, so
`uncoded body` prints its definition. The agent reads the earlier definition
from the stub or the file.

## Expected faults

### `uvx` is missing

`uncoded refs` starts ty through `uvx`, and `uvx` is not on the path. uncoded
says that `uvx` was not found, and to install uv. It exits with status `1`. The
user installs uv, or the agent finds references by other means.

### ty fails

ty cannot be fetched, for example on a first run with no network, or cannot
start, fails, or stops responding. `uncoded refs` stops and says that ty failed,
passing on what ty or `uvx` said about why. If ty stops responding,
`uncoded refs` gives up after 60 seconds and says so. It exits with status `1`
and never blames the `--in` file. The agent tries again later, or finds
references by other means.

### A generated file cannot be written

`uncoded sync` cannot write or remove a generated file, for example for lack of
permission or space. It stops, says in one line which file and why, and exits
with status `1`. Files it had already written stay as they are. Once the cause
is fixed, running `uncoded sync` again puts everything right, and until then
`uncoded check` reports the generated files as stale.
