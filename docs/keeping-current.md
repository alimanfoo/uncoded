# Keep the index current

Run this after changing indexed Python code or Markdown docs, and before your
agent navigates again:

```sh
uvx uncoded sync
```

Run it once in every fresh checkout too. The index is local and is not in Git.

## Refresh on commit

Add this entry to the `repos` list in `.pre-commit-config.yaml`, after any
formatters that change indexed files:

```yaml title=".pre-commit-config.yaml"
- repo: local
  hooks:
    - id: uncoded
      name: uncoded
      entry: uvx uncoded sync
      language: system
      always_run: true
      pass_filenames: false
```

Install the hooks once:

```sh
uvx pre-commit install
```

`always_run` also refreshes the index when a commit only deletes files. If the
hook updates tracked skill files, stage those files and commit again.

The hook keeps the index current at commit time. During a task, you or your
agent still need to run `sync` after an edit and before using the index.

## Check without writing

```sh
uvx uncoded check
```

Exit status `0` means the generated files match a fresh build. Status `1` means
files would change, or the configuration is invalid. Run `sync` to refresh the
index, then check again.
