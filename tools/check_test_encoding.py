"""Enforce encoding= on every text read/write in tests/.

Checks tests/*.py for calls to .read_text(), .write_text(), and text-mode
open() that lack an encoding= keyword argument. Exits non-zero on any
violation so pre-commit can block the commit.

Covers fixture-derived receivers such as (tmp_path / "f.py").write_text(...)
that PLW1514 misses because ruff cannot infer the Path type through pytest
fixture injection.
"""

import ast
import sys
from pathlib import Path


def _open_mode(call: ast.Call) -> str | None:
    """Return the literal mode string from an open() call, or None.

    Returns None when the mode argument is absent or not a string literal.
    """
    if len(call.args) >= 2:
        arg = call.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        return None
    for kw in call.keywords:
        if kw.arg == "mode":
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
            return None
    return None


def check_file(path: Path) -> list[str]:
    """Return one error string per violation found in path."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as e:
        return [f"{path}: cannot read: {e}"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}: SyntaxError: {e.msg}"]

    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        has_encoding = any(kw.arg == "encoding" for kw in node.keywords)

        if isinstance(func, ast.Attribute) and func.attr in ("read_text", "write_text"):
            if not has_encoding:
                errors.append(f"{path}:{node.lineno}: .{func.attr}() missing encoding=")

        elif isinstance(func, ast.Name) and func.id == "open":
            mode = _open_mode(node)
            # Skip binary-mode open(); "b" anywhere in the mode string means binary.
            if mode is not None and "b" in mode:
                continue
            if not has_encoding:
                errors.append(f"{path}:{node.lineno}: open() missing encoding=")

    return errors


def main() -> int:
    """Run the check over tests/ and return an exit code."""
    tests_dir = Path("tests")
    if not tests_dir.is_dir():
        print(f"error: tests/ not found in {Path.cwd()}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for py_file in sorted(tests_dir.glob("*.py")):
        all_errors.extend(check_file(py_file))

    for err in all_errors:
        print(err, file=sys.stderr)

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
