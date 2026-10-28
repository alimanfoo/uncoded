# Compatibility

uncoded's contract is the part of uncoded that a project can rely on from one
release to the next. The version number of each release says whether it changes
the contract in a way that can break a project. This page says what the contract
covers and what each kind of release can change. [Upgrading](upgrading.md) says
how to upgrade a project, and [the changelog](changelog.md) lists the changes in
each release.

## The contract

The contract covers:

- each command, its flags and its exit statuses;
- the data that a command prints on standard output, such as the source that
  `uncoded body` prints and the references that `uncoded refs` prints;
- each configuration key;
- each generated file's path, and the layout of the namespace map, the docs map
  and the stubs;
- what each uncoded skill tells the agent to do; and
- the Python versions that uncoded runs on.

The contract does not cover the messages that a command prints, or their
wording, wherever the command prints them. These include the lines in which
`uncoded sync` names the files it wrote, the line in which `uncoded check` says
whether the index is current, and the warnings about files that `uncoded sync`
skipped. Nor does it cover uncoded's Python modules. Run uncoded through its
commands, not by importing it.

## Versions

The package version is the only version. The index and the uncoded skills have
no version of their own.

### Major releases

A release is major, such as 4.0.0 after 3.x, when it changes the contract in a
way that can break a project. That is when it:

- removes or renames a command, a flag, a configuration key or a generated
  file's path, or changes its meaning or its default;
- changes an exit status, or the format of the data that a command prints on
  standard output;
- changes how a generated file is laid out, such as how its keys nest or which
  keys end in `/`, but not which symbols or headings it lists;
- changes what a skill tells the agent to do, by removing, reversing or
  narrowing an instruction, or by reordering the steps of a workflow;
- removes a feature that an earlier release deprecated; or
- drops support for a Python version.

### Minor releases

A release is minor, such as 3.1.0 after 3.0.x, when it adds a command, a flag, a
configuration key, a generated file or new guidance in a skill, or deprecates a
feature. A deprecated feature keeps working, with a warning, until a major
release removes it.

### Patch releases

A release is a patch, such as 3.0.2 after 3.0.1, when it fixes uncoded so that
it does what its documentation or its skills say. For example, a patch can
correct a skill to match the commands, list a symbol that the index missed, or
reword a skill without changing what it tells the agent to do.

A patch can therefore change the generated files, even though it changes no rule
for how they are laid out.

### Unclear cases

Where a change could fit more than one kind of release, the effect that it is
expected to have on projects decides.
