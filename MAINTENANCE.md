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
