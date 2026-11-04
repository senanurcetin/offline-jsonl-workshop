# Releasing `jsonl-utf8-guard`

Releases go to PyPI through [Trusted Publishing](https://docs.pypi.org/trusted-publishers/). No API token is stored in this repository.

## One-time setup (repository owner only)

1. On PyPI, open *Your account → Publishing → Add a new pending publisher*:
   - PyPI project name: `jsonl-utf8-guard`
   - Owner: `senanurcetin`, repository: `offline-jsonl-workshop`
   - Workflow: `release.yml`, environment: `pypi`
2. On GitHub, open *Settings → Environments → New environment* and name it `pypi`. Optionally add yourself as a required reviewer.

## Each release

1. Bump `version` in `pyproject.toml` and move the `Unreleased` entries in `CHANGELOG.md` under the new version. Merge this through a PR with green CI.
2. Create a GitHub Release with tag `vX.Y.Z`. The tag must match the version; the workflow checks this.
3. `release.yml` runs the tests and `verify_release.py`, builds the sdist and wheel, and publishes them.

If the PyPI publisher has not been set up yet, the publish job fails and nothing is uploaded. The GitHub Release itself is unaffected.
