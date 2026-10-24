# Engineering standard

This brief develops [GH257](https://github.com/alimanfoo/uncoded/issues/257) and
its comments.

## What do I want to be able to do?

I want uncoded to meet the engineering standards of top-tier contemporary open
source projects, and to stay there. I want to be able to say what that means,
measure it, and see where the project falls short.

## What's wrong or missing today?

The code is in good shape. The suite passes at full branch coverage, every
pre-commit hook passes, and releases use Trusted Publishing. But nothing written
down says what standard uncoded holds itself to, so nothing measures it and
nothing stops it drifting. Practices that dreamcatcher already follows are
missing here: workflows pinned to commits, automated dependency updates, tests
on more than one operating system and the current Python versions, branch
protection, a changelog, a compatibility policy, and a release checklist. The
[record on GH257](https://github.com/alimanfoo/uncoded/issues/257#issuecomment-6390803545)
lists 36 specific suggestions.

## What has to be true of anything I'd accept?

uncoded has an enduring engineering standard in `docs/standard.md`. It is
adapted from
[dreamcatcher's standard](https://github.com/alimanfoo/dreamcatcher/blob/main/docs/standard.md),
with a measure, a bar and a check for each criterion. The criteria transfer
selectively:

- S1 to S5, C1, C3, K2 to K4, and E1 to E4 transfer as they are.
- C4 covers the agent-facing contract: the generated skills, the index formats,
  and the commands, flags, output and exit statuses of the command-line tool.
- C2 names uncoded's own enduring documents.
- K1 covers the few structural rules uncoded has, such as the one module that
  spawns a subprocess and the path boundary.
- A new family of criteria covers the infrastructure: the supply chain,
  supported platforms and Python versions, packaging, and releases.

Dreamcatcher's infrastructure is the floor. Each of the further suggestions on
GH257 is considered on its merits as the criteria are written.

The package version is the only version. Any breaking change to the agent-facing
contract needs a major release. A change is breaking when it removes or changes
a command, a flag, an exit status or an output format, changes an artefact's
path or shape, or changes what a skill tells an agent to do. Additions are minor
releases, and wording changes are patches. A compatibility statement says this
where users will find it.

uncoded has an ontology that fixes its vocabulary, so that agents and I use the
same word for the same thing.

The work follows dreamcatcher's
[engineering standard phase](https://github.com/alimanfoo/dreamcatcher/issues/330):
write the standard, measure a baseline, close the gaps in ordered stages, and
keep the standard in force through a definition of done in every pull request
and a release checklist that remeasures each major or minor release.
Specifications live in dated folders under `specs/`, starting with this one.

## What limits this?

The open issues that overlap this work, such as #223, #231, #234, #205 and #179,
become part of it rather than being duplicated.

## How will I know it worked?

The standard is written, a measurement against every criterion is recorded, and
each shortfall is either closed or an issue. The release checklist runs the
measurement again before each major or minor release.

## What's still open?

- Whether Windows and macOS are supported platforms.
- Which exemplar projects, if any, the standard names beyond dreamcatcher's.
- Whether the work changes no behaviour except where a stage says so, as
  dreamcatcher's phase required.
