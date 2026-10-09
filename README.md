# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords, skim
the first few lines of files, and fill gaps from pretraining rather than reading
the actual code. The result is plausible-looking output built on a hallucinated
understanding of the code.

**uncoded** builds a static navigation index that gives coding agents
progressively deeper views of a codebase. Agents start with a map of every
symbol, read compact stubs when they need signatures and types, and retrieve
only the symbol bodies that they need. Each view adds detail without making the
agent read whole source files.

The `uncoded body` command retrieves symbol bodies, and `uncoded refs` finds
every reference to a symbol. References cover callers, dead-symbol checks, and
the full set of sites to update before a rename.

Read the [documentation](https://alimanfoo.github.io/uncoded/) for installation,
configuration, command reference, upgrades, and contributor guidance.
