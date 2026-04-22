# Maintenance notes

Things noticed but not fixed — kept here so the next maintainer can
weigh them deliberately rather than rediscover them by surprise.

## setup-serena does not refresh an existing serena entry

If a repo's `.mcp.json` already has `mcpServers.serena`, `setup-serena`
leaves it alone rather than bumping it to the current `SERENA_VERSION`
or updating args. Rationale: overwriting could stomp user
customisation (extra args for their env). Users who want to refresh
must delete the entry and re-run. Reconsider if this bites — the
natural fix is an explicit `--refresh` flag rather than changing the
silent default.

## Repo's own LSP config is hand-written, not template-generated

`.mcp.json`, `.serena/project.yml`, and `.claude/settings.json` at the
repo root predate `setup-serena` and carry commentary that the minimal
templates in `serena_setup.py` don't. `TestRepoDogfooding` catches
drift on the contract bits (version pin, allowlist coverage, project
YAML required fields), but the commentary lives in one place only. A
future cleanup could either regenerate the files (losing the
commentary) or promote the commentary into `serena_setup.py` so it
lives next to the templates that generate the real thing.
