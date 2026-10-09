---
hide:
  - toc
---

<div class="home-intro" markdown="1">

# Give your agent a map of your codebase

uncoded indexes Python code and Markdown docs. It gives your coding agent
progressively deeper views of Python code. A map shows the indexed symbols,
compact stubs add parameters and types, and `uncoded body` returns exact source
on demand. The agent stops as soon as one view gives it enough information.

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

The map is the first view. It shows that `greet` exists and where to find it.
When the agent needs the function's parameters and return type, it reads the
generated stub:

```python title=".uncoded/stubs/src/greetings.pyi (excerpt)"
def greet(name: str) -> str:
    ...
```

When the agent needs the exact source, it retrieves that body without reading
the rest of the source file:

```sh
uvx uncoded body greet --in src/greetings.py
```

Broad questions may need only the map. Questions about names and types may stop
at the stub.

Before a rename, `uncoded refs` finds the references to check and update.
Markdown docs get a separate map of files and headings.

The index stays local. The generated navigation skills are committed with your
project so agents know how to use it.
