# uncoded

AI coding agents navigate codebases poorly. They grep for guessed keywords, skim
the first few lines of files, and fill gaps from pretraining rather than reading
the actual code. The result is plausible-looking output built on a hallucinated
understanding of the code.

**uncoded** builds a static navigation index that gives coding agents
progressively deeper views of a codebase. Agents start with the namespace map,
read compact stubs when they need parameters and types, and retrieve only the
symbol bodies that they need. Each view adds detail without making the agent
read whole source files.

Read the [documentation](https://alimanfoo.github.io/uncoded/) for installation,
configuration, command reference, upgrades, and contributor guidance.
