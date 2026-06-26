"""EncodingWarning gate sentinel.

Guards both fail-open vectors of the runtime encoding gate.

The gate has two parts: PYTHONWARNDEFAULTENCODING=1 causes the interpreter
to emit EncodingWarning on text IO without encoding=, and
filterwarnings = ["error::EncodingWarning"] in pyproject.toml escalates
that warning to an exception.

This test fails loudly if either part is missing. With both present the
escalated warning is raised and caught (pass). With PYTHONWARNDEFAULTENCODING
unset nothing is emitted and nothing is raised (DID NOT RAISE, red). With the
filterwarnings line removed the warning is emitted but not escalated, so
nothing is raised (DID NOT RAISE, red).
"""

from pathlib import Path

import pytest


def test_encoding_warning_gate(tmp_path: Path) -> None:
    """Fail if PYTHONWARNDEFAULTENCODING is unset or the error filter is absent."""
    with pytest.raises(EncodingWarning):
        (tmp_path / "sentinel.txt").write_text("x")
