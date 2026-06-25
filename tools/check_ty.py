"""Run ty check at the pinned version, using TY_VERSION from uncoded.refs.

This wrapper lets the pre-commit ty hook derive the version from the same
constant that governs the ty LSP server. The two cannot drift. Exits with
ty's return code.
"""

import subprocess  # noqa: S404 -- subprocess used to invoke the ty check
import sys

from uncoded.refs import TY_VERSION


def main() -> int:
    """Run the ty check at the pinned version and return ty's exit code."""
    result = subprocess.run(  # noqa: S603 -- fixed command vector; uvx resolved from PATH by design
        ["uvx", "--from", f"ty=={TY_VERSION}", "ty", "check", "src", "tests"],  # noqa: S607 -- uvx resolved from PATH by design
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
