import subprocess
import sys
import textwrap

import pytest

# The start of every stand-in for ty: functions that read one LSP message from
# uncoded and send one back.
_STAND_IN_PRELUDE = r"""
import json
import os
import sys


def read_message():
    headers = b""
    while not headers.endswith(b"\r\n\r\n"):
        headers += sys.stdin.buffer.read(1)
    length = int(headers.split(b":")[1])
    return json.loads(sys.stdin.buffer.read(length))


def send(body):
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    sys.stdout.buffer.flush()


INITIALIZE_RESPONSE = json.dumps(
    {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
).encode()
"""


@pytest.fixture
def stand_in_for_ty(*, monkeypatch):
    """Return a function that makes uncoded refs start a script in place of ty.

    The script runs under the test's Python, after the stand-in prelude, with
    the pipes that uncoded refs would give uvx.
    """
    popen = subprocess.Popen

    def use(*, script):
        source = _STAND_IN_PRELUDE + textwrap.dedent(script)
        monkeypatch.setattr(
            subprocess,
            "Popen",
            lambda *_args, **kwargs: popen([sys.executable, "-c", source], **kwargs),
        )

    return use
