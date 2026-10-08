# Contributing

Use Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

## Set up a checkout

```sh
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync --extra dev
uv run uncoded sync
uv run pre-commit install
```

The development extra includes tests, linting, type checking, documentation, and
pre-commit tools. The local index is ignored by Git, so build it before
navigating the checkout.

On Windows, enable symbolic links before cloning:

```sh
git config --global core.symlinks true
```

This lets Git check out `CLAUDE.md` as the symbolic link to `AGENTS.md`.

## Run the tests

```sh
PYTHONWARNDEFAULTENCODING=1 uv run pytest -q --tb=short
```

The suite requires complete branch coverage. The environment variable enables
`EncodingWarning`, which the test configuration turns into an error.

For a focused run without the repository-wide coverage gate:

```sh
PYTHONWARNDEFAULTENCODING=1 uv run pytest -q --tb=short tests/test_stubs.py --no-cov
```

## Run the checks

```sh
uv run pre-commit run --all-files
```

The suite runs formatters, linters, type and complexity checks, the strict
documentation build, and `uncoded sync`. If a hook changes files, stage the
changes and run the suite again. Never commit with `--no-verify`.

## Edit the docs

```sh
uv run mkdocs serve
```

Preview the site at `http://127.0.0.1:8000/`. Run `uv run mkdocs build` to check
links, anchors, and navigation. The strict build treats warnings as errors.

## Change indexed content

After editing Python code or indexed Markdown, run `uv run uncoded sync` before
navigating again. Commit any changed generated skill files with the sources that
produced them. Read `AGENTS.md` for the code and testing conventions.

## Release

Publish a GitHub release from its version tag. `.github/workflows/publish.yml`
builds the source distribution and wheel and uploads them with PyPI Trusted
Publishing. The repository does not store a PyPI token.
