"""Generate the uncoded-review skill file for the target repository."""

from pathlib import Path

from uncoded.sync import sync_file

SKILL_OUTPUT = Path(".claude/skills/uncoded-review/SKILL.md")

_SKILL_CONTENT = """\
---
name: uncoded-review
description: "Perform a coherence review of a Python codebase: a diagnostic sweep \
for semantic drift, naming inconsistency, promissory mismatch, and structural \
incoherence. Produces a Markdown report of findings with verbatim evidence and \
confidence levels, for human investigation. Assumes uncoded is installed \
(.uncoded/namespace.yaml and .uncoded/stubs/ present)."
---

# Coherence Review

A diagnostic sweep of a Python codebase for specific, observable symptoms of
semantic drift and incoherence. Output is a structured Markdown report of
candidate regions, each with verbatim evidence and a confidence level, for a
human to investigate. Not a bug hunt, not a lint pass, not a refactor.

## Why coherence, and what you are looking for

A codebase accumulates corruption differently from how it accumulates bugs. Bugs
announce themselves — tests fail, users complain, exceptions raise. Corruption
passes every integrity check. It is the slow divergence between what the code
claims to mean and what it actually does, between how one part of the codebase
names a concept and how another names the same concept, between an architecture
as declared and an architecture as practised. Each local decision that
contributed to it was reasonable. The accumulation is not.

Corruption's one observable signature is **internal inconsistency**. Not
absolute wrongness — that requires a reference outside the code, which is not
available here. Just pairwise disagreement between things that ought to agree:
a name and its behaviour, two names for the same concept, a docstring and the
signature it sits on, a declared architecture and the actual import graph. Every
symptom in the sweeps below is a form of inconsistency. The review's job is to
find these disagreements — not to diagnose root cause and not to fix them.

## What this skill is not

- **Not a bug-finder.** Bugs are the job of testing and code review. A coherence
  review can run on code that passes every test and still find plenty.
- **Not a style pass.** Tabs versus spaces, docstring format, import ordering —
  irrelevant. Linters exist.
- **Not a refactor.** No proposing fixes, no suggesting renames, no rewriting
  code. The output is findings. The human decides what to do with them.
- **Not a general code review.** Performance, security, correctness — out of
  scope unless they happen to manifest as a coherence symptom.

## Prerequisites

Verify by reading `.uncoded/namespace.yaml` — if it exists and is non-empty,
proceed. If not, stop and tell the user to run `uncoded sync` first; the review
depends on the index.

If Serena MCP tools are available (`mcp__serena__*`), the structural sweep has
more leverage. The review still works without Serena but will be weaker on
cross-file reference checks.

## Workflow

The review proceeds in four sweeps, each building on the previous:

1. **Orient** — load the navigation index and form a mental map.
2. **Lexical sweep** — read the namespace, look for naming-level inconsistency.
3. **Promissory sweep** — read stubs, check each symbol's name / signature /
   docstring for internal disagreement.
4. **Structural sweep** — combine namespace and imports to find boundary and
   shape symptoms.

Do the sweeps in order. Write findings as you go — do not hold them in memory
until the end.

## Step 1: Orient

Read `.uncoded/namespace.yaml` in full. This is the map — directories, files,
classes, methods, functions — in source order. Do not skim. Every public symbol
in the codebase is listed here, and the shape of the namespace itself is
evidence.

While reading, note:

- The vocabulary the codebase uses for its core concepts
- The organisational logic (domain-driven? layered? feature-based? ad hoc?)
- Anything that surprises you — odd names, asymmetric organisation, suspicious
  clusters

Also read `CLAUDE.md` if present, and follow any repo-specific navigation
protocol throughout the review.

Before starting the sweeps, tell the user how many public symbols were indexed.
Then proceed without asking for further confirmation.

## Step 2: Lexical sweep

Working from the namespace alone, look for four categories of naming-level
symptom.

**Concept duplication under different names.** The same concept referred to by
different names in different parts of the codebase. Examples: `fetch_user`,
`get_user`, `load_user`, `retrieve_user` all appearing as separate functions
doing substantively the same thing. `compute_*`, `calculate_*`, `derive_*` used
interchangeably. Two classes called `UserRecord` and `AccountProfile` that
model the same entity.

Detection: scan the namespace for symbol clusters with verb or noun overlap.
Where suspicion arises, spot-check the relevant stubs to confirm they overlap
in meaning.

**Qualifier accretion.** Names carrying modifiers that are fossils of
iteration: `_new`, `_v2`, `_updated`, `_legacy`, `_real`, `_proper`, `_final`,
`_fixed`. Also prefix forms: `new_`, `old_`, `real_`. These are almost always
worth flagging — someone needed to distinguish a new thing from an old thing
and the distinction was never resolved.

Detection: scan the namespace for these qualifier patterns.

**Vocabulary islands.** A subregion of the codebase (a directory, a module
cluster) using a distinct vocabulary that doesn't overlap with the rest. Often
the result of an unintegrated contribution, or a session that added a feature
without looking outward.

Detection: look for directories whose namespace entries share few word-roots
with the rest of the codebase.

**Collision with drift.** The same name appearing in multiple places with
subtly different meanings — visible as different signatures, different docstring
content, or different domain associations.

Detection: identify name collisions in the namespace, then examine the stubs to
see whether the uses agree.

## Step 3: Promissory sweep

Working from stubs, examine each public symbol's name / signature / docstring
triple for internal disagreement.

For each non-trivial public symbol (skip trivial one-liners and `__init__` with
no meaningful body):

**Name–signature mismatch.** Does the name's verb fit the signature's return? A
function called `validate_*` that returns the validated object rather than
raising or returning bool. A `get_*` that mutates. A noun-named thing that is a
verb's worth of work. A boolean-returning function whose name doesn't start with
`is_`, `has_`, `can_`, or similar.

**Docstring–signature mismatch.** Does the docstring refer to parameters not in
the signature, or fail to mention parameters that are? Does the docstring
describe return behaviour that contradicts the type annotation?

**Docstring–name mismatch.** Does the docstring describe an operation noticeably
more specific, more general, or simply different from what the name advertises?
"Normalises and validates the record" on a function called `check_record`.

**Defensive docstrings.** Docstrings that warn about the function rather than
describe it. "Note: this does not actually X despite the name." "Do not use
this for Y; use Z instead." These are confessions — someone noticed drift and
documented it rather than fixing it.

The stub itself is the evidence. Quote the stub excerpt (name, signature,
first-line docstring) verbatim in the finding.

## Step 4: Structural sweep

Combine the namespace with the import graph and, if available, Serena's
reference resolution.

**Overgrown public surfaces / god modules.** A module or class whose public
namespace is much larger than its siblings, or spans obviously different
concerns. Look for outlier symbol counts: a file with forty public symbols where
its neighbours have five; a class with thirty methods covering multiple domains.

**Boundary violations.** One module importing private symbols (leading
underscore) from another. Scan `from module import _thing` patterns across
stubs' import sections. Each instance is a finding.

**Cross-vocabulary imports.** Imports that cross domain boundaries in suspicious
directions — a `core/` or `utils/` module importing from a specific business
domain; a module in domain A importing from domain B when those domains appear
meant to be independent. Flag candidates and note the direction; let the human
decide.

**Zero-caller public symbols.** A public symbol (no leading underscore) with no
references anywhere in the codebase. Either dead code or an unused API surface.

Check systematically, not by spot-check:

1. From the namespace map, list all public symbols in each source module.
2. Cross-reference with stub import sections — any symbol imported by another
   source module is live; remove it from the candidate list. This culls the
   obvious cases cheaply.
3. For remaining candidates, use Serena's `find_referencing_symbols` to verify.
   If Serena is unavailable, note findings as lower confidence.
4. Distinguish two sub-cases when reporting:
   - *No callers anywhere* — dead code; highest priority.
   - *Callers only in tests* — the symbol is tested but not used in source;
     may be an exposed internal that should be private.

**Redundant public surface.** A public constant and a public parameterless
function in the same module where the function's sole body is `return
<constant>`. Both symbols being public exposes an implementation detail
unnecessarily — only one needs to be public. Detection: look for parameterless
public functions with a trivial single-line body, then check whether they
return a public symbol from the same module.

## Report format

Save the report as `.uncoded/reviews/coherence-review-YYYY-MM-DD.md`, using
today's date (timestamped to preserve previous runs). Create the directory if
it does not exist.

Use this structure:

```markdown
# Coherence Review — <repo name>

**Date:** YYYY-MM-DD
**Symbols indexed:** N
**Sweeps run:** lexical, promissory, structural
**Findings:** N total (N lexical · N promissory · N structural)

## Priority regions

Regions with two or more findings — examine these first:

- `path/to/file.py` — N findings
- ...

*(Omit this section if no region has more than one finding.)*

## Findings

### 1 · <symptom summary>

**Category:** lexical | promissory | structural
**Symptom:** concept-duplication | qualifier-accretion | vocabulary-island |
  collision-with-drift | name-signature-mismatch | docstring-signature-mismatch |
  docstring-name-mismatch | defensive-docstring | god-module |
  boundary-violation | cross-vocabulary-import | zero-caller
**Location:** `path/to/file.py` · `ClassName/method_name` · L12–L34
**Confidence:** high | medium | low

**Evidence:**
> Verbatim quote from namespace.yaml, stub, or import statement.

One or two sentences describing the inconsistency. Not a diagnosis. Not a fix.

---

### 2 · ...
```

## Principles

**Coverage, not filtering.** Report every finding at its confidence level. Do
not silently drop findings judged low-severity. A low-confidence finding with
clear evidence is useful — the human can filter. A dropped finding is not.

**Confidence is part of the finding, not a gate.**

- `high` — the inconsistency is explicit; evidence is directly in the stub or
  namespace
- `medium` — strongly implied but depends on judgement about intent
- `low` — pattern-based suspicion that needs human interpretation

**Evidence must be verbatim.** Quote the relevant namespace line, stub excerpt,
or import statement exactly. A finding the human cannot quickly verify is worse
than no finding.

**One finding per inconsistency.** If a single symbol has a name–signature
mismatch and a docstring–name mismatch, that is two findings on the same
symbol, not one combined finding. Let the report show the density.

**Do not propose fixes.** No renaming suggestions, no refactoring proposals, no
"this should be moved to". The finding describes what is inconsistent. The
human owns remediation.

**Do not flag style.** Docstring format, type annotation style, import ordering,
naming conventions — out of scope. Coherence is about semantic consistency, not
surface consistency.

**Do not fabricate.** Every finding must be anchored to code you actually
examined. If a sweep suggests a pattern but you cannot find concrete instances,
do not include it.

## Scope control

If the codebase has more than ~1000 public symbols:

1. Complete the lexical sweep in full (the namespace is compact enough).
2. For the promissory sweep, prioritise: core domain modules (identified from
   the namespace structure), any module that appeared in a lexical finding, and
   a representative sample of the rest (~30% of remaining stubs).
3. For the structural sweep, focus on the module and package level first,
   descending to individual symbols only where the higher-level scan raised
   flags.

Note the scope chosen in the report summary so the human knows what was and was
not examined.

## Examples

<example>
<scenario>Three public functions: `fetch_user(id)`, `get_user_by_id(id)`,
`load_user(user_id)`, in three different files, all returning a User and all
doing substantively the same lookup.</scenario>
<flag>Yes. Concept duplication, high confidence. Evidence: three stub excerpts
quoted verbatim.</flag>
</example>

<example>
<scenario>A function `validate_user(user)` whose signature returns `User` rather
than `bool` or `None`, and whose docstring says "Validates and returns the user
if valid, raising UserValidationError otherwise."</scenario>
<flag>Yes. Name–signature mismatch, medium confidence. The name reads as a
predicate but the behaviour is a validator-filter. Stub quoted as
evidence.</flag>
</example>

<example>
<scenario>Two modules, `storage/cache.py` and `runtime/memoize.py`, both
defining functions that wrap callables with LRU caching, with slightly different
cache-size defaults.</scenario>
<flag>Yes. Concept duplication, medium confidence. Both stubs quoted. Note the
difference — the human may determine it is intentional.</flag>
</example>

<example>
<scenario>A class `OrderProcessor` with 34 methods spanning order creation,
validation, payment capture, fulfilment dispatch, refund handling, and
reporting.</scenario>
<flag>Yes. God module, high confidence. Method list quoted from
namespace.</flag>
</example>

<example>
<scenario>A function uses `x` as a parameter name in a mathematical formula
module.</scenario>
<flag>No. Short variable names in mathematical contexts are conventional and do
not indicate drift.</flag>
</example>

<example>
<scenario>A function is 80 lines of non-trivial logic.</scenario>
<flag>No, not by itself. Complexity is not incoherence. Flag only if the
complexity manifests as inconsistency — e.g. the function's behaviour has
drifted from what its name or docstring promise.</flag>
</example>

<example>
<scenario>The codebase uses both `Optional[X]` and `X | None` in different
files.</scenario>
<flag>No. Both are valid Python and mean the same thing. Flag only if the
semantics of absence differ — e.g. some functions return None on failure while
others raise, for the same kind of operation.</flag>
</example>
"""


def sync_skill(*, check: bool) -> bool:
    """Write the uncoded-review skill file if it differs from what's on disk."""
    return sync_file(SKILL_OUTPUT, _SKILL_CONTENT, check=check)
