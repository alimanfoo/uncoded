# Keep the index current

The index is local and is not in Git. Agents keep it current: the navigation
skills tell an agent to run `uncoded sync` at the start of every session, after
it changes indexed Python code or Markdown docs, and whenever it notices that
something else has changed files, such as a pull or a checkout.

## Refresh on commit

A pre-commit hook that runs `uncoded sync` refreshes the index on every commit,
and fails the commit when it changes an installed skill file. Stale installed
skill files then cannot be committed without anyone noticing.

Add this entry to the `repos` list in `.pre-commit-config.yaml`, after any
formatters that change indexed files:

```yaml title=".pre-commit-config.yaml"
- repo: local
  hooks:
    - id: uncoded
      name: uncoded
        entry: uv run uncoded sync
      language: system
      always_run: true
      pass_filenames: false
```

Install the hooks once:

```sh
uv run pre-commit install
```

`always_run` also refreshes the index when a commit only deletes files. If the
hook updates installed skill files, stage those files and commit again. A CI job
that runs the same pre-commit hooks catches what a local commit missed.

The project's `uv.lock` pins the version of uncoded that writes the committed
skill files, so that every machine commits the same files.

## Check without writing

```sh
uv run uncoded check
```

`uncoded check` reports whether the generated files are current, without
changing anything. Exit status `0` means they are current. Status `1` means
files would change, the configuration is invalid, or a generated file cannot be
read.

The index is never committed, so in a fresh checkout, such as CI's,
`uncoded check` always reports it as stale. Use the pre-commit hook in CI
instead.
