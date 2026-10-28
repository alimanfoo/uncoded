# Testing

uncoded's test suite combines small tests of each module with tests of each
command and tests at the boundary with ty. Each technique answers a different
question, and no single number is treated as proof that uncoded is correct.

## What the tests establish

### Branch coverage

The suite measures branch coverage over `src/` and fails below 100%. In CI, the
coverage of every test job is combined first, so a branch that only one
operating system or Python version takes still counts. This establishes that the
suite executes every branch in uncoded's source. It helps expose untested
alternatives and dead code. It does not establish that the assertions are
sufficient, or that every possible input was tried.

### Encoding failures

The interpreter is armed to emit `EncodingWarning`, and pytest treats that
warning as an error. A sentinel test in `tests/test_encoding_gate.py` fails when
the gate is not armed. This catches a file or subprocess operation that the
suite executes and that relies on the platform's default text encoding. It says
nothing about a line that the suite does not execute.

### Commands on a real file system

The tests in `tests/test_cli.py` run each command through `main` in a temporary
project directory, with real files, and check what the command prints, the files
that it writes and its exit status. They hold the behaviour and the exit
statuses that [the stories](stories.md) describe. They do not run the installed
`uncoded` command.

### Modules on their own

Most other test modules each test one module of `src/uncoded/`, such as the
stubs, the docs map or the configuration search. These tests pin down the cases
that are slow or awkward to reach through a command. They do not show that the
module is wired into a command.

### A stand-in for ty

`uncoded refs` runs the ty language server through `uvx`. The `stand_in_for_ty`
fixture in `tests/conftest.py` makes it start a Python script instead, with the
same pipes. The script answers deterministically, so the tests can check how
`uncoded refs` frames its messages, reads ty's answers, and reports ty when it
fails or exits early. These tests do not show that ty itself still answers as
the script does.

## Integration tests

The tests marked `integration` run the real ty language server, at the version
that `uncoded refs` pins, through `uvx`. They need `uvx` on `PATH`, and the
first run may download ty. They establish that `uncoded refs` finds the
references that it promises with that version of ty. Run them after any change
to the pinned version. The default run leaves them out, because they spawn a
process and are slower than the rest.

## Hung tests

Every test has a time limit to finish, counting its fixture setup and teardown.
`timeout` in `pyproject.toml` sets the limit, and CI raises it on the systems
that run slower. The limit is there to end a run that has hung, not to measure
speed.

When the limit passes, `pytest-timeout` writes the stack of every thread to the
terminal. On Linux and macOS it then fails the test, and the run carries on. On
Windows it ends the whole run.

## What CI runs

For every push and pull request to `main`, the
[CI workflow](https://github.com/alimanfoo/uncoded/blob/main/.github/workflows/ci.yml)
runs the whole suite, the integration tests included, with the encoding gate on
every supported operating system and Python version. It then combines the
coverage of those jobs and checks it against 100%. It runs every pre-commit
hook, and then `uncoded check`. The hooks include a strict build of the
documentation site and the regeneration of the `--help` blocks in
[the commands reference](commands.md). On every supported operating system, it
builds the sdist, builds the wheel from the sdist, and runs `uncoded --version`
from the wheel.

For every pull request, the
[dependency review workflow](https://github.com/alimanfoo/uncoded/blob/main/.github/workflows/dependency-review.yml)
checks the dependencies that the pull request adds or changes for known
vulnerabilities. For every push to `main`, the
[docs workflow](https://github.com/alimanfoo/uncoded/blob/main/.github/workflows/docs.yml)
builds the documentation site and publishes it to GitHub Pages.

## Run the tests

The
[Commands section of the agent guide](https://github.com/alimanfoo/uncoded/blob/main/AGENTS.md#commands)
gives the commands that run the tests.
