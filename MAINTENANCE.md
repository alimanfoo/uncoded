# Maintenance notes

## Release publishing

GitHub releases publish to PyPI through `.github/workflows/publish.yml`.
The workflow uses PyPI Trusted Publishing, so it does not need a `PYPI_TOKEN`
or any other long-lived publishing secret.

The PyPI trusted publisher is configured for:

- PyPI project: `uncoded`
- Owner: `alimanfoo`
- Repository: `uncoded`
- Workflow: `publish.yml`
- Environment: `pypi`

To release, create and publish a GitHub release from the release tag. The
`published` release event builds the source distribution and wheel, then
uploads them to PyPI.

## Deferred work

Things noticed but not fixed — kept here so the next maintainer can weigh them
deliberately rather than rediscover them by surprise.

Nothing currently deferred.
