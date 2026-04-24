# Coherence Review — uncoded

**Date:** 2026-04-25
**Symbols indexed:** ~200 (source + tests)
**Sweeps run:** lexical, promissory, structural
**Findings:** 8 total (1 lexical · 4 promissory · 3 structural)

## Priority regions

Regions with two or more findings — examine these first:

- `src/uncoded/stubs.py` — 3 findings (L1, P1, S1)
- `src/uncoded/instruction_files.py` — 2 findings (P4, S2)
- `src/uncoded/extract.py` — 2 findings (P3, S1 involves it)

---

## Findings

### L1 · `build_*` verb used with inconsistent semantics

**Category:** lexical
**Symptom:** collision-with-drift
**Location:** `src/uncoded/namespace_map.py` · `build_map` · `src/uncoded/stubs.py` · `build_stubs`
**Confidence:** medium

**Evidence:**
> `def build_map(modules: list[ModuleInfo]) -> dict:  # L37-73`
> `"""Build a nested dict representing the namespace."""`
>
> `def build_stubs(source_root: Path, output_dir: Path, *, check: bool) -> int:  # L374-423`
> `"""Sync stub files for all symbols under source_root, removing any orphans."""`

`build_map` constructs and returns a data structure (pure computation). `build_stubs` writes files to disk and removes orphans (a sync/IO operation). Both use the `build_*` prefix, but the prefix means something different in each case. Elsewhere, IO-writing operations consistently use `sync_*` (`sync_file`, `sync_instruction_file`, `sync_skill`).

---

### P1 · `build_stubs` name says "build", docstring says "Sync"

**Category:** promissory
**Symptom:** docstring-name-mismatch
**Location:** `src/uncoded/stubs.py` · `build_stubs` · L374
**Confidence:** high

**Evidence:**
> `def build_stubs(source_root: Path, output_dir: Path, *, check: bool) -> int:  # L374-423`
> `"""Sync stub files for all symbols under source_root, removing any orphans."""`

The function is named `build_stubs` but its docstring opens with "Sync stub files" — the same verb used by `sync_file`, `sync_instruction_file`, and `sync_skill` for analogous operations. The docstring accurately describes what the function does; the name does not. Compound with L1.

---

### P2 · `setup_serena` docstring mentions "ty" but name only says "serena"

**Category:** promissory
**Symptom:** docstring-name-mismatch
**Location:** `src/uncoded/serena_setup.py` · `setup_serena` · L181
**Confidence:** low

**Evidence:**
> `def setup_serena(root: Path | None) -> int:  # L181-203`
> `"""Generate Serena + ty + Claude Code configuration under ``root``."""`

The name `setup_serena` implies the function concerns Serena only, but the docstring discloses it also generates configuration for `ty` (a type checker) and Claude Code. The name understates the scope of the function.

---

### P3 · `base` parameter undocumented in `iter_source_files` and `walk_source`

**Category:** promissory
**Symptom:** docstring-signature-mismatch
**Location:** `src/uncoded/extract.py` · `iter_source_files` · L100; `walk_source` · L118
**Confidence:** medium

**Evidence:**
> `def iter_source_files(source_root: Path, base: Path | None) -> Iterator[tuple[str, str]]:  # L100-115`
> `"""Yield (source_text, rel_path) for every Python file under *source_root*."""`
>
> `def walk_source(source_root: Path, base: Path | None) -> list[ModuleInfo]:  # L118-137`
> `"""Walk a source root and extract symbols from all Python files."""`

Both functions accept a `base` parameter that is absent from their docstrings. A reader of either stub has no description of what `base` controls or when to pass it.

---

### P4 · `generate_section` name implies dynamic generation; body is `return SECTION`

**Category:** promissory
**Symptom:** name-signature-mismatch
**Location:** `src/uncoded/instruction_files.py` · `generate_section` · L104
**Confidence:** low

**Evidence:**
> `def generate_section() -> str:  # L104-106`
> `"""Return the full delimited uncoded section for an instruction file."""`
>
> *(Serena confirms the body is: `return SECTION`)*

`generate_section()` takes no arguments and returns the pre-computed module-level constant `SECTION`. The name `generate_*` implies dynamic construction; the implementation is a trivial accessor. Compound with S2.

---

### S1 · `stubs.py` imports private symbol `_property_kind` from `extract.py`

**Category:** structural
**Symptom:** boundary-violation
**Location:** `src/uncoded/stubs.py` (import) · `src/uncoded/extract.py` · `_property_kind`
**Confidence:** high

**Evidence:**
> `from uncoded.extract import _property_kind, iter_source_files`
> *(first line of stubs.pyi imports section)*

`_property_kind` carries a leading underscore, marking it as a private implementation detail of `extract.py`. `stubs.py` imports it directly, crossing the boundary. Either `_property_kind` should be made public (if it is genuinely shared logic), or its functionality should be replicated or moved so the boundary holds.

---

### S2 · `SECTION` is public but has no callers outside its own module

**Category:** structural
**Symptom:** zero-caller
**Location:** `src/uncoded/instruction_files.py` · `SECTION` · L101
**Confidence:** medium

**Evidence:**
> `SECTION = f'{MARKER_START}\n{_SECTION_BODY}\n{MARKER_END}\n'  # L101`
>
> *(Serena confirms: only references are within `instruction_files.py` itself — the module-level definition and `generate_section`'s body)*

`SECTION` is a public constant (no leading underscore) but is only used internally: as the return value of `generate_section()`. External callers use `generate_section()`, not `SECTION` directly. The constant and the function are both public, creating redundancy. Compound with P4.

---

### S3 · `read_project_name` in `serena_setup.py` reads from `pyproject.toml`, the remit of `config.py`

**Category:** structural
**Symptom:** cross-vocabulary-import
**Location:** `src/uncoded/serena_setup.py` · `read_project_name` · L94
**Confidence:** low

**Evidence:**
> `def read_project_name() -> str:  # L94-104`
> `"""Read the project name from pyproject.toml, falling back to the cwd name."""`
>
> `# config.py contains:`
> `def find_pyproject_toml() -> Path | None:`
> `def read_source_roots() -> list[Path]:`
> `def read_instruction_files() -> list[Path]:`

`read_project_name` reads from `pyproject.toml` using the same `find_pyproject_toml` helper as `config.py`. The other `read_*` functions that read from `pyproject.toml` live in `config.py`. `read_project_name` lives in `serena_setup.py`, which is the only module with a `read_*` function that doesn't belong to `config.py`.
