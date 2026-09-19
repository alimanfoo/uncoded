# Documentation Navigation

This codebase uses [uncoded](https://github.com/alimanfoo/uncoded) to maintain a
documentation index.

**Step 1: Orient. Read the docs map first.** Before answering the user, before
any other tool call:

```text
Read .uncoded/docs.yaml
```

`.uncoded/docs.yaml` is an orientation outline: it lists every Markdown file and
its heading hierarchy. Read it in full, now.

**Step 2: Navigate.** Headings in the map are literal text. Use `Read` or `grep`
to navigate to a specific section identified in the map.

**Step 3: Refresh.** After every modification to indexed Markdown, run the
repository's configured `uncoded sync` command before the next
documentation-navigation operation. The modification can change the heading map.
