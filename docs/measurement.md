# Measurement

This page holds the latest measurement of uncoded against
[the standard](standard.md). Each measurement replaces the one before it, and
earlier measurements are in Git history.

This is the first measurement, the baseline. It was taken on 2026-10-27 at
`0071673`, the commit on `main` after the stories were added in #290 and before
any gap was closed. A stage of the engineering standard roadmap (#257) owns most
shortfalls below. The rest go to the product owner: three are open bugs that no
stage owns, and one, the test names, was raised on the pull request that took
this measurement, #306.

## Results

| Criterion                  | Measured                                                                                                                         | Status  | Owner                                |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------ |
| Cohesive modules           | 0 modules without one nameable responsibility; the largest are `stubs.py` (471 lines) and `cli.py` (377)                         | met     |                                      |
| Focused functions          | 0 functions without one nameable job; the longest is `refs._run_exchange` (88 lines)                                             | met     |                                      |
| No unused exports          | 20 public names that no other module imports, besides `main`                                                                     | not met | #273                                 |
| One way                    | 2 facts derived more than once: the project directory, 3 ways, and which statements are symbols, 3 ways                          | not met | #273, #296                           |
| No suppressions            | 4 `noqa`, 0 `type: ignore`, 0 `pragma: no cover`; no hook against `noqa` or `type: ignore`                                       | not met | #269, #267                           |
| One vocabulary             | 25 disagreements, besides 6 that are behaviour changes not yet built; 337 uses of a replaced word, 217 of them `project_root`    | not met | #272                                 |
| True documents             | 14 behaviour changes the stories settle are not yet built; 3 open bugs contradict a story                                        | not met | #265, #293 to #304; #280, #281, #292 |
| Docs by purpose            | Tutorial, how-to pages, references and development pages are kept apart; no user page links to a development page                | met     |                                      |
| Versioned contract         | No compatibility statement and no changelog; `docs/upgrading.md` covers the two major releases                                   | not met | #264                                 |
| Accurate references        | No generated `--help` blocks; 2 behaviours that a reference or skill describes differently from the code                         | not met | #274; #292                           |
| Machine-checked rules      | 3 of the 6 rules checked; removals outside `sync.py` at 4 places; 286 functions with positional parameters                       | not met | #269, #270                           |
| Fast readable tests        | 368 tests in 2.07 seconds at 100% branch coverage; 18 of 326 distinct test names name a mechanism, not a behaviour               | not met | product owner, #306                  |
| Current tracker            | 7 of 46 open issues fall short: 4 use a replaced word, and 4 ask for work done or ruled out                                      | not met | #272, #275                           |
| Reviewed changes           | 11 pull requests merged since v3.0.0, 10 linking an issue or spec, 0 answering the definition of done; 4 commits outside one     | not met | #275                                 |
| Loud failures              | No `strict = true`, `pytest>=8.0`, no test timeout                                                                               | not met | #269                                 |
| Rules not cases            | No ledger; 4 conditionals name a situation, each with a cause inside uncoded                                                     | not met | #273, #293, #296, #304               |
| Invariants by construction | 0 branches that defend against a state the types could rule out; 5 class fields admit `None`                                     | met     |                                      |
| Few concepts               | 35 terms on the concepts page, settled with the product owner in #279 and #290; no other change has added one                    | met     |                                      |
| Symmetry                   | 4 asymmetries between `uncoded body` and `uncoded refs`, and between the code and documentation index paths; skills are parallel | not met | #273, #296                           |

## Notes

- **Cohesive modules, focused functions.** Review read every module under `src`,
  largest first, and named one responsibility for each: `stubs.py` builds the
  stubs, `cli.py` defines and runs the commands, `refs.py` finds references
  through ty, `resolver.py` finds a symbol by its name path, `skill.py` writes
  the skills, `docs_map.py` builds the docs map, `config.py` finds and reads the
  configuration file, and `extract.py` lists the symbols of Python files. The
  longest functions each do one job:

  | Function                                | Lines | Its job                                      |
  | --------------------------------------- | ----: | -------------------------------------------- |
  | `refs._run_exchange`                    |    88 | Run one exchange with ty's language server.  |
  | `cli.main`                              |    78 | Define the command-line grammar.             |
  | `cli._sync`                             |    74 | Run `uncoded sync` or `uncoded check`.       |
  | `cli._sync_code_artefacts`              |    56 | Write or remove the code index.              |
  | `docs_map.extract_headings`             |    40 | List a Markdown file's headings.             |
  | `stubs.build_stubs`                     |    39 | Write the stubs for one source root.         |
  | `skill._sync_one_skill`                 |    38 | Write or remove one skill's installed files. |
  | `resolver.resolve_ast_node_from_source` |    37 | Find the definition that a name path names.  |
  | `namespace_map.build_map`               |    37 | Build the namespace map's tree.              |
  | `docs_map.build_docs_map`               |    37 | Build the docs map's tree.                   |

- **No unused exports.** No other module under `src` imports these public names:
  `config.Config`, `docs_map.DOCS_HEADER`, `docs_map.extract_headings`,
  `extract.ClassInfo`, `extract.extract_module`, `namespace_map.HEADER`,
  `refs.Reference`, `refs.TY_VERSION`, `resolver.resolve_ast_node`,
  `skill.SKILLS`, `skill.SKILL_ROOTS`, `skill.Skill`, `stubs.StubAssignment`,
  `stubs.StubClass`, `stubs.StubFunction`, `stubs.StubModule`,
  `stubs.StubParam`, `stubs.VALUE_WIDTH_CAP`, `stubs.extract_stub` and
  `stubs.render_stub`. Some are used in their own module or reached through a
  return value, and the tests import others. Stage 15 (#273) makes each one
  private or gives it an importer.
- **One way.** The project directory is found three ways. `config.py` walks up
  the tree once in `find_pyproject_toml` and again in `_find_config_file`
  (#234), and `refs._find_root` falls back to the nearest `pyproject.toml`, or
  the `--in` file's directory, when there is no configuration file. Which
  statements in a module body or class body are symbols is decided three times,
  in `extract.py`, `stubs.py` and `resolver.py`, and `extract.ModuleInfo` and
  `stubs.StubModule` are two models of a Python file's symbols. Stage 15 (#273)
  owns these, and stage 13.4 (#296) removes the fallback in `refs.py`.
- **No suppressions.** The four `noqa` comments are the subprocess waivers in
  `refs.py` (S404, S603, S607) and `tests/test_refs.py` (S404). Stage 11 (#269)
  moves them to per-file ignores, and stage 9 (#267) adds the hooks against
  blanket `noqa` and `type: ignore`.
- **One vocabulary.** The consistency review reported 31 disagreements, one for
  each pair of conflicting claims, however many places repeat a claim. Six of
  them are behaviour changes that the stories settle and the code does not yet
  do, such as `uncoded init` and `uncoded refs` listing a symbol's definition,
  and are counted under true documents. Of the other 25, 20 are about words: 13
  use a word the concepts page replaces, such as "config file", "artefact" and
  "root type", and 7 use a concept's word for something else, such as "symbol"
  for a directory or "index" for every generated file. The other 5 are claims
  about a symbol that its code contradicts, such as the `sync.py` docstring
  naming an `uncoded --check` flag that does not exist, and `AGENTS.md`
  promising a stub for every Python file. Words that the concepts page replaces
  occur 337 times: 95 in prose and 242 in identifiers, of which 217 are
  `project_root` and its variants. Stage 14 (#272) settles all of these.
- **True documents.** The design's Stories section lists 14 behaviour changes
  that the stories settle and the code does not yet do. Stage 7 (#265) builds
  paths that use `/` on every system, and stages 13.1 to 13.12 (#293 to #304)
  build the rest. Three open bugs contradict a story, and no stage owns them:
  #280, where `uncoded check` reports the index as current after a source root
  is removed; #281, where a name path with a slash reaches a class that a later
  definition redefines; and #292, where `uncoded body` changes CRLF line endings
  and drops a byte-order mark. The architecture contradicts nothing, but it does
  not yet state the three layers, which stage 11 (#269) adds. The standard names
  some checks that are not yet in place, and each is listed under its criterion
  here with the stage that adds it.
- **Docs by purpose.** "Get started" is the tutorial, "Use uncoded" holds the
  how-to pages, and "Reference" holds the configuration, command and upgrading
  references. The README sends the reader to the site. `docs/contributing.md`
  sits under "Development", and stage 10 (#268) removes it.
- **Versioned contract.** Stage 6 (#264) writes the compatibility statement and
  the changelog. The stories also record two **Breaking** changes to come, which
  stage 13.4 (#296) and stage 7 (#265) build.
- **Accurate references.** `docs/commands.md` has no block generated from
  `--help`, and stage 16 (#274) adds them with cog. Review read
  `docs/commands.md`, `docs/configuration.md` and the three skill sources
  against the code and the `--help` output. One behaviour is described
  differently: `docs/commands.md` says `uncoded body` prints the source "exactly
  as written in the file", and the code navigation skill says its output is
  "byte-identical to disk", but #292 shows it is not for a file with CRLF line
  endings or a byte-order mark. No stage owns #292. And the documentation
  navigation skill says the headings in the docs map are literal text, but the
  docs map adds a suffix such as " (2)" to a repeated heading. Stage 16 (#274)
  reviews the skills against the code.
- **Machine-checked rules.** Three rules are checked today: only `refs.py`
  imports `subprocess` (ruff's S404, with the waivers above), every generated
  file carries the provenance marker (`tests/test_markers.py`), and every text
  read and write names its encoding (PLW1514 and the runtime gate). Three are
  not. Files and directories are removed outside `sync.py` at four places: three
  `rmdir` calls in `stubs.py` and one in `skill.py`. Imports already point down
  the three layers, with no middle-layer module importing another, but nothing
  checks it. Stage 11 (#269) checks both. Ruff's PLR0917, with
  `max-positional-args = 0`, finds 48 functions with positional parameters in
  `src` and 238 in `tests`, and stage 12 (#270) makes them keyword-only.
- **Fast readable tests.** The default run passed 368 tests in 2.07 seconds, as
  pytest reports it, at 100% statement and branch coverage. The 8 integration
  tests, which spawn ty, passed in 0.77 seconds. Review read all 326 distinct
  test names and found 18 that name a function, a type or a step of a protocol
  that a user never sees: `test_extract_params_covers_input_kind`,
  `test_render_param_covers_input_kind`, `test_docs_gate_builds_when_docs_true`,
  `test_docs_gate_skips_when_docs_false`,
  `test_gate_unmet_removal_prunes_empty_directory`, `test_happy_path_dispatch`,
  `test_parses_framed_message`,
  `test_renderer_supplies_separator_for_body_without_leading_newline`,
  `test_returns_frozen_dataclass`,
  `test_returns_lsp_locations_when_popen_succeeds`, `test_skill_registry`,
  `test_skips_notifications_until_matching_id`, `test_lsp_error_raises`,
  `test_raises_on_closed_stream`, `test_kills_on_timeout`, `test_import`,
  `test_file_not_found_propagates` and `test_syntax_error_propagates`. No stage
  of the roadmap renames tests for the behaviour they test, so this goes to the
  product owner.
- **Current tracker.** Four open issues use a word the concepts page replaces:
  #162 ("artefact"), #231 and #235 ("contributor"), and #280 ("up to date").
  Four ask for work that is done or that a story rules out: #162, since
  `.uncoded/.gitignore` now ignores everything under `.uncoded/`; #226, which
  rests on `tools/check_encoding.py`, now gone; #229, whose docstring was
  corrected; and #278, which asks for names defined inside an `if` that the
  stories say are not symbols. Stage 14 (#272) corrects the words, and stage 17
  (#275) triages the rest.
- **Reviewed changes.** v3.0.0 is the previous major or minor release. Of the 11
  pull requests merged since, #252 links no issue or spec, and none answers the
  definition of done, which stage 17 (#275) starts asking for. Four commits
  reached `main` outside a pull request, the last on 2026-10-24. Branch
  protection now requires a pull request, enforced for admins.
- **Loud failures.** Stage 11 (#269) adds `strict = true`, raises the floor to
  `pytest>=9.0` and adds the timeouts.
- **Rules not cases.** These conditionals name a situation, and the cause of
  each is a choice uncoded made: `config._config_file_at` passes over a
  directory named `.uncoded`, and stops the search at a `pyproject.toml` without
  `[tool.uncoded]`, which stage 13.1 (#293) changes; `skill.py` removes the
  skill names of earlier versions, which stage 13.12 (#304) stops; and
  `refs._find_root` falls back when there is no configuration file, which stage
  13.4 (#296) removes. Stage 15 (#273) starts the ledger and settles any that
  remain. The other conditionals apply rules from outside uncoded, such as
  CommonMark's headings and Python's parameter syntax, or rules the concepts
  page states, such as a property's setter and deleter not being symbols.
- **Invariants by construction.** The class fields that admit `None` are
  `resolver.NamePath.tail`, `stubs.StubParam.annotation`,
  `stubs.StubFunction.return_annotation`, `stubs.StubAssignment.annotation` and
  `stubs.StubAssignment.value_source`. Each `None` is a case the source can
  produce, such as a name path with no slash or a parameter with no annotation.
  `stubs.StubAssignment` also carries an `is_pep695_alias` flag, and its fields
  allow an alias with an annotation, which no source produces, but no branch
  defends against it.
- **Few concepts.** The concepts page was written with the product owner in #279
  and #290, and nothing else has changed it.
- **Symmetry.** `uncoded body` and `uncoded refs` each list the exceptions they
  report, and the lists can drift (#205). `uncoded refs` finds a project
  directory and `uncoded body` does not, which stage 13.4 (#296) settles. In
  `cli.py` the code index is built root by root and the documentation index from
  all roots at once, and the project directory is passed to
  `extract.iter_source_files` by name but to `docs_map.iter_doc_files` by
  position. Stage 15 (#273) owns the rest. The two navigation skills have the
  same steps in the same order.

## Method

Each number above was taken this way, from the project directory of a checkout
with the development dependencies installed.

- **Line counts** come from `wc -l src/uncoded/*.py`. Function lengths, public
  names that no other module imports, and class fields that admit `None` come
  from the script below, run with `uv run python`. Its counts are prompts for
  review, which judges each against the bar.

  ```python
  import ast
  from pathlib import Path

  trees = {
      p.stem: ast.parse(p.read_text(encoding="utf-8"))
      for p in Path("src/uncoded").glob("*.py")
  }
  imported = {
      (node.module.removeprefix("uncoded."), alias.name)
      for tree in trees.values()
      for node in ast.walk(tree)
      if isinstance(node, ast.ImportFrom) and node.module
      for alias in node.names
  }
  functions, unimported, nullable = [], [], []
  for module, tree in trees.items():
      for node in ast.walk(tree):
          if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
              start = min([node.lineno] + [d.lineno for d in node.decorator_list])
              functions.append((node.end_lineno - start + 1, f"{module}.{node.name}"))
          if isinstance(node, ast.ClassDef):
              for field in node.body:
                  if isinstance(field, ast.AnnAssign) and "None" in ast.unparse(
                      field.annotation
                  ):
                      nullable.append(f"{module}.{node.name}.{ast.unparse(field.target)}")
      for node in tree.body:
          names = [node.name] if isinstance(node, ast.FunctionDef | ast.ClassDef) else []
          if isinstance(node, ast.Assign | ast.AnnAssign):
              targets = node.targets if isinstance(node, ast.Assign) else [node.target]
              names = [t.id for t in targets if isinstance(t, ast.Name)]
          unimported += [
              f"{module}.{name}"
              for name in names
              if not name.startswith("_") and (module, name) not in imported
          ]
  print("Longest functions:", *sorted(functions, reverse=True)[:10], sep="\n  ")
  print("Public names no other module imports:", *sorted(unimported), sep="\n  ")
  print("Class fields that admit None:", *sorted(nullable), sep="\n  ")
  ```

- **Suppressions** come from
  `grep -rn "noqa\|type: ignore\|pragma: no cover" src tests`.
- **Positional parameters** come from
  `uv run ruff check --preview --select PLR0917 --config 'lint.pylint.max-positional-args=0' --statistics src`,
  and the same command over `tests`.
- **Writes and removals outside `sync.py`** come from
  `grep -nE "\.(write_text|write_bytes|unlink|rmdir|mkdir|rename|replace|touch)\(|shutil" src/uncoded/*.py`.
- **Imports between modules** come from
  `grep -n "^from uncoded" src/uncoded/*.py`, read against the layers in the
  design.
- **Test time and coverage** come from
  `PYTHONWARNDEFAULTENCODING=1 uv run pytest -q`, and the integration tests'
  from `PYTHONWARNDEFAULTENCODING=1 uv run pytest -q -m integration --no-cov`.
  The distinct test names come from `uv run pytest --collect-only -q -m ""`,
  with parameters stripped.
- **Vocabulary** comes from the consistency review, run by an agent following
  the `uncoded-consistency-review` skill over `src`, `tests`, `README.md`,
  `AGENTS.md`, `docs` and the skill sources, with the concepts page as the
  authority, and the specifications and generated files left out. The review
  counts one disagreement for each pair of conflicting claims, however many
  places repeat a claim. Replaced words come from a case-insensitive search of
  the files that Git tracks in the same places, apart from the concepts page,
  for each word after "Replaces:" on the concepts page, in prose and in
  identifiers such as `project_root`, with a phrase allowed to break across
  lines. A use of "body" or "source" is counted only when it means a whole
  definition or a skill source, which review decides, and the command name
  `uncoded body` is not counted.
- **The tracker** comes from `gh issue list --state open`, each title and body
  searched for the replaced words, plurals included, and read against the code
  and the stories.
- **Reviewed changes** come from `git log --first-parent v3.0.0..origin/main`
  and from the bodies of the pull requests merged since v3.0.0, read through
  `gh pr list --state merged`.
- **Branch protection** comes from
  `gh api repos/alimanfoo/uncoded/branches/main/protection`.
- **True documents, accurate references, rules not cases and symmetry** come
  from review: the stories and the design's Stories section read against the
  code, `docs/commands.md`, `docs/configuration.md` and the skill sources read
  against the code and each command's `--help`, every conditional under `src`
  read for the situation it names, and the namespace map read for parallel
  operations.
