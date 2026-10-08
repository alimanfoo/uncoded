---
hide:
  - toc
---

<div class="home-intro" markdown="1">

# Give your agent a map of your codebase

uncoded indexes Python code and Markdown docs. Your coding agent sees the names
and structure before it starts reading, then uses exact tools to retrieve source
and find references.

[Get started](getting-started.md){ .md-button .md-button--primary }
[How agents use it](agent-workflow.md){ .home-secondary }

</div>

## What the agent sees

For a repository containing this function, uncoded generates a map with its name
and location.

<div class="home-example" markdown="1">

<div markdown="1">

### Your source

```python title="src/greetings.py"
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

</div>

<div markdown="1">

### The map

```yaml title=".uncoded/namespace.yaml (excerpt)"
src/:
  greetings.py:
    greet:
```

</div>

</div>

The agent reads the map to locate `greet`, checks its signature in the generated
stub, and retrieves the implementation when it needs it:

```sh
uvx uncoded body greet --in src/greetings.py
```

Before a rename, `uncoded refs` finds the references to check and update.
Markdown docs get a separate map of files and headings.

The index stays local. The generated navigation skills are committed with your
project so agents know how to use it.
