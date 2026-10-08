# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords, skim
the first few lines of files, and fill gaps from pretraining rather than reading
the actual code. The result is plausible-looking output built on a hallucinated
understanding of the code.

**uncoded** builds a static navigation index for the codebase. Agents load it at
the start of a task and navigate directly to what they need, without guessing or
grepping.

It also ships `uncoded body` to read symbol bodies and `uncoded refs` to find
every reference to a symbol. References cover callers, dead-symbol checks, and
the full set of sites to update before a rename.

Read the [documentation](https://alimanfoo.github.io/uncoded/) for installation,
configuration, command reference, upgrades, and contributor guidance.
