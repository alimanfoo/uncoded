"""EncodingWarning gate sentinel.

Fails loudly if PYTHONWARNDEFAULTENCODING is not set. The
filterwarnings = ["error::EncodingWarning"] gate in pyproject.toml is
inert when the env var is absent, because the interpreter never emits
EncodingWarning without it. This test makes that silent disable loud.
"""

from pathlib import Path

import pytest


def test_encoding_warning_gate(tmp_path: Path) -> None:
    """Fail if PYTHONWARNDEFAULTENCODING is not set."""
    with pytest.warns(EncodingWarning):
        (tmp_path / "sentinel.txt").write_text("x")
