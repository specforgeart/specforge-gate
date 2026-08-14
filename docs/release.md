# Release process

SpecForge Gate uses Git tags plus `.github/workflows/release.yml` for GitHub Releases.

## Current release

The current public patch release is:

```text
v0.3.3
```

`v0.3.0` remains the first public alpha/MVP baseline. The Python package version and runtime
`specforge_gate.__version__` are both `0.3.3`.

## Release invariants

Before a release tag is pushed:

- the hardening change is merged to `main`;
- `pyproject.toml` and `specforge_gate.__version__` match;
- the changelog contains the release version and date;
- canonical Windows checks have passed on the hardening branch;
- all required pull-request checks are green.

The tag workflow then independently:

1. verifies that `v<project.version>` matches the pushed tag;
2. verifies that the tagged commit is reachable from `main`;
3. bootstraps on GitHub-hosted Linux;
4. runs `bash scripts/check.sh`;
5. builds the wheel and source distribution;
6. writes SHA-256 checksums;
7. creates the GitHub Release and uploads all `dist/*` assets.

## Publish v0.3.3

After the patch PR is merged and `main` is verified:

```bash
git fetch origin main --tags
git tag -a v0.3.3 <verified-main-sha> -m "SpecForge Gate v0.3.3"
git push origin v0.3.3
```

Do not move or recreate a published release tag.

## Expected GitHub Release assets

The release is expected to contain:

```text
specforge_gate-0.3.3-py3-none-any.whl
specforge_gate-0.3.3.tar.gz
SHA256SUMS
```

This release process does not publish to PyPI. GitHub Release assets are the distribution channel
for `v0.3.3`.

## Failure handling

If the tag workflow fails, do not retag another commit with the same version. Inspect the failed
Release workflow, fix the problem through the normal Issue/PR process, and decide explicitly
whether to delete/recreate an unpublished tag or advance to a new version.

If a GitHub Release already exists for the same valid tag, rerunning the tag workflow uploads
`dist/*` with `--clobber`; published tag movement remains prohibited.

## Post-release posture

After `v0.3.0` publishes successfully, treat it as the frozen first public MVP baseline. Do not
start new product-surface work solely because it exists in the backlog. New work requires explicit
user evidence, an integration need, or a measured quality/security/reliability gap.
