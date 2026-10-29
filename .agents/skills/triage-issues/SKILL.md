---
name: triage-issues
description:
  Triage uncoded's GitHub issues with the product owner, using their preferred
  questions, pace and engineering judgment. Use when discussing which issues
  deserve work and refining them for implementation.
---

# Triage issues

Please help me to triage issues.

Before you start, read the "How we decide" section of `AGENTS.md`, and judge
every proposed change by it. Read [the concepts page](../../../docs/concepts.md)
and [the stories](../../../docs/stories.md) too: the stories say what uncoded
promises, and the concepts page says what the words mean.

## Questions for each issue

Here are some questions we should ask of every issue:

1. **What would the user actually do?** Identify a realistic situation, not
   merely an input a function could receive.
2. **What did we promise?** Distinguish broken behaviour from unsupported use or
   a request for more capability.
3. **What actually happens?** Inspect real output, reproduce the case, and
   explain the mechanism precisely.
4. **What change would help?** Check that the proposed fix preserves meaning and
   does not introduce disproportionate complexity.
5. **What should the implementing agent be told?** Settle the intended
   behaviour, give practical engineering guidance, and specify meaningful tests.

Don't invent or guess at anything. Bring data.

These questions guide your investigation. They are not the shape of your reply.

## Pace and responsibility

Please tutor me through one issue and one decision at a time. I cannot absorb
much information at once. Keep explanations short and concrete, and develop them
through the conversation.

Treat it as a conversation. Open each issue with only what the issue is, as you
understand it after investigating, in a few sentences. Then give the two
strongest options, each in a line or two, and recommend one. The second option
is the best real alternative, not a default such as doing nothing, unless doing
nothing is that alternative. Take one decision per turn: when an
issue raises several points, take them one at a time, each in the same shape.
Don't end every turn with a question; I will follow up.

Act as the experienced lead. Investigate and make a recommendation where you
can, rather than standing back and waiting for me to direct routine next steps.
My questions should refine the decision rather than uncover missing groundwork.

After recording the outcome for an issue, move automatically to the next one
unless I ask to pause or change the task.

Read current GitHub state when resuming, including the comments and labels.
Check whether the decision was already made and only dispatch remains; do not
repeat triage just because an issue is still open. Do not maintain a session
checkpoint.

Take up only issues with no outcome label, unless I name one. A
`blocked-externally` issue needs only the check described below.

## Labels and dispatch

Keep issue type, triage outcome and dispatch separate.

Use one primary type: `bug`, `enhancement` or `maintenance`. After triage, give
an open issue one current outcome:

- `needs-info`: facts such as reproduction steps, logs or a concrete example are
  missing, so a decision cannot yet be made.
- `needs-discussion`: the issue needs further discussion or design before
  acceptance for implementation.
- `ready-to-implement`: I have agreed to implementation, and the scope, expected
  behaviour and acceptance criteria are sufficiently clear for an agent to
  proceed.
- `blocked-externally`: I have agreed to the work, but it waits on something
  outside this repository, such as an upstream release. Leave a comment that
  names the event to wait for and what to do when it happens. In later sessions,
  check only whether that event has happened. Once it has, replace the label
  with `ready-to-implement`.

Replace the previous outcome when the decision changes; do not leave conflicting
outcomes on an issue. Apply an outcome only after triage. For `needs-info` or
`needs-discussion`, leave a short comment naming exactly what is missing or
undecided, unless an existing comment already records it. An idea may remain
open for discussion without being ready to implement. Close an issue when triage
decides against the work, and record why; link the existing issue when it is a
duplicate.

Readiness does not dispatch work. When dispatch is authorized, assign the issue
to me and apply the chosen dispatch label. Ask which skill only when it has not
already been chosen; do not ask again for an action I have authorized. Preserve
existing dispatch labels unless I request a change.

## Judgments

Be skeptical of agent-raised issues. Do not invent a supported workflow to
justify one.

The same skepticism applies to an issue's facts and proposed fix. Check its
premises against current code and data, because an issue may already be fixed
or its evidence may be out of date. Test the proposed fix, and the exceptions it
leaves, rather than inherit them.

When an issue records my own request in an agent's words, confirm the scope with
me before refining it. An agent can widen a request beyond what I asked for.

Look for earlier decisions before recommending. Search closed issues and pull
requests on the same mechanism, the specifications under `specs/`, and the
project documents.

A bug contradicts a story, including the handling it promises for a user error
or expected fault. Ask whether the current response breaks a promise or whether
the proposal asks for a stronger promise. Behaviour a story explicitly accepts
is not a bug.

Look past the reported instance to the family it belongs to, and prefer the fix
that makes like things uniform. One rule that covers every case can remove a
special case, unwanted behaviour and code together.

When an issue is a race or a case of fault handling, ask first whether a change
of design would remove its whole class, before refining a fix for the one
instance.

Any new concept, architectural mechanism or conditional branch warrants deeper
inspection. Ask whether the user benefit justifies the added complexity and
whether existing rules can do the job. Keep strong pressure against adding
machinery.

When a fix needs a special case, and that case needs another, stop. Find a rule
that holds unconditionally, or accept the cost.

A clear failure can be sufficient. For rare damaged-state cases, reporting the
problem and asking the user to repair it may be better than adding recovery,
failure isolation or partial reports. Record an accepted limitation in the
stories.

Do not dismiss maintenance merely because nothing currently malfunctions. Better
types can express intended semantics, and distinct failure types can reflect
real differences between failures.

Look at real output before deciding a formatting issue is either useful or
hypothetical.

Output must earn its place. Before improving how something is shown, ask whether
it should be shown at all.

Establish what each item represents before changing its grouping or treating it
as a duplicate. Preserve distinctions that matter to the user; similar names or
appearances do not establish duplication.

Check the meaning of a proposed simplification. A change that looks like a
simplification can change what a path, a name or a message means.

Do not stop at "unverified locally" when platform documentation establishes the
mechanism and existing CI can exercise it. Read the docs or propose a focused
test, not prolonged speculation about Windows behaviour.

Prefer the standard library or established third-party libraries. Give the
implementing agent a practical direction rather than leaving a list of
unresolved approaches.

When triage settles product behaviour, require the decision in the stories as
part of implementation. An issue or code condition alone is not where the
project's lasting account of that behaviour belongs. Current behaviour is not
automatically endorsed behaviour: distinguish what happens today, accepted
limitations and unresolved questions. Keep an unresolved question explicit in
the stories, with a pointer to its discussion issue, rather than describing it
as intended functionality.

Use GitHub and the current project documents for the latest product decisions.
