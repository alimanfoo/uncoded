# Contributing

The repository uses Python 3.12 or later and [uv](https://docs.astral.sh/uv/)
for environments, commands, and builds.

## Set up a checkout

```sh
git clone https://github.com/alimanfoo/uncoded
cd uncoded
uv sync --extra dev
uv run uncoded sync
uv run pre-commit install
```

The development extra includes the test, lint, type-check, documentation, and
pre-commit tools. Run `uncoded sync` before navigating the checkout because the
local index is ignored by Git.

## Run the tests

```sh
PYTHONWARNDEFAULTENCODING=1 uv run pytest
```

The environment variable enables Python's `EncodingWarning`. Pytest promotes
that warning to an error, and a sentinel test fails when either half of the gate
is missing. The suite requires complete branch coverage.

For a focused test run that should not enforce repository-wide coverage, use
`--no-cov`:

```sh
PYTHONWARNDEFAULTENCODING=1 uv run pytest tests/test_stubs.py --no-cov
```

## Run the checks

```sh
uv run ruff check --fix
uv run ruff format
uv run mkdocs build
uv run pre-commit run --all-files
```

The pre-commit suite also runs the type checker, both complexity checkers, the
Markdown formatter and linter, and `uncoded sync`. If a hook changes a file,
stage the result and run the suite again. Do not skip hooks when committing.

Use `uv run mkdocs serve` while editing the site. The strict build treats a
broken link, missing anchor, or page omitted from the navigation as an error.

## Change indexed content

Run `uv run uncoded sync` after each source or indexed documentation edit and
before using the index again. The command refreshes the ignored local index and
may refresh tracked skill files. Commit a changed skill file with the source
that generated it.

## Release

GitHub releases publish the package through `.github/workflows/publish.yml`.
Create a release from its version tag and publish it. The workflow builds the
source distribution and wheel, then uses PyPI Trusted Publishing to upload them.
The repository does not store a PyPI token.
