"""Build a YAML doc map from Markdown files for agent orientation."""


def extract_headings(text: str) -> list[tuple[int, str]]:
    """Return the ATX headings in ``text`` as ordered (level, title) pairs.

    Recognises ATX headings only: 1–6 ``#`` followed by a space and a
    non-empty title. Trailing runs of ``#`` are stripped. Lines inside
    fenced code blocks (opened by a line starting with ```` ``` ```` or
    ``~~~``, closed by the matching marker) are not headings. Setext
    underlines are never recognised.

    Corners not in the criterion:
    - Indented headings: the ``#`` must be at column 0; leading spaces
      are not stripped.
    - Fence lengths: fences are matched by their first three characters
      (````` ``` ````` or ``~~~``), regardless of the exact number of
      backticks or tildes.
    """
    headings: list[tuple[int, str]] = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        if in_fence:
            if line.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue

        if line.startswith("```") or line.startswith("~~~"):
            in_fence = True
            fence_marker = line[:3]
            continue

        if not line.startswith("#"):
            continue

        # Count consecutive leading #.
        level = 0
        while level < len(line) and line[level] == "#":
            level += 1

        # Valid ATX: 1–6 # followed by exactly one space.
        if level > 6 or level >= len(line) or line[level] != " ":
            continue

        title = line[level + 1 :].rstrip().rstrip("#").rstrip()
        if title:
            headings.append((level, title))

    return headings
