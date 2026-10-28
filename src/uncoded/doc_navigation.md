# Documentation Navigation

This codebase uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain a
documentation index.

**Step 1: Orient. Sync, then read the docs map.** Run the project's configured
`uncoded sync` command, so that the map is current. Then, before answering the
user and before any other tool call:

```text
Read .uncoded/docs.yaml
```

`.uncoded/docs.yaml` is an orientation outline: it lists every Markdown file and
its heading hierarchy. Read it once, in full, at session start.

**Step 2: Navigate.** Headings in the map are literal text. Use `Read` or `grep`
to navigate to a specific section identified in the map. A repeated heading
under one parent ends with a " (N)" suffix, which is not in the file. To
navigate to it, grep the heading text and take the Nth match under that parent.

**Step 3: Refresh.** After every modification to indexed Markdown, run the
project's configured `uncoded sync` command before the next
documentation-navigation operation. The modification can change the docs map.
Run it too whenever you notice that something else has changed files, such as a
pull, a checkout, or another agent working in the same project.
