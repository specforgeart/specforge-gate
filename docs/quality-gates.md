# Quality gates

SpecForge Gate uses a fast pull-request gate plus scheduled dependency auditing. The goal is to make merge decisions depend on stable, meaningful checks without repeating expensive work unnecessarily.

## Pull-request architecture

The required merge path is:

```text
PR
├─ CI / static-package
├─ CI / tests (3.11)
├─ CI / tests (3.12)
├─ CI / tests (3.13)
│  └─ CI / ci-gate
├─ Windows Quality / windows-quality
├─ Action Smoke / action-smoke
├─ PR Policy / pr-policy
├─ Dependency Review / dependency-review
└─ CodeQL
```

`ci-gate` is the stable Linux aggregate check. Static analysis and package validation run once, while runtime compatibility tests run independently on Python 3.11, 3.12, and 3.13. The aggregate fails unless both the one-time quality/package job and the entire compatibility matrix succeed.

`action-smoke` is one stable integration gate. It covers a passing explicit specification, a report-only failing specification, and pull-request Markdown selection.

Windows Quality continues to execute the canonical Windows bootstrap and check scripts.

## Coverage

Canonical pytest verification collects line and branch coverage and enforces a total floor of 85%. Branch coverage is enabled with `--cov-branch` so untested decision paths are visible even when their containing lines execute.

## Supply-chain controls

Third-party Actions used by repository workflows and the public composite action are pinned to reviewed full commit SHAs. Human-readable release comments remain beside each SHA, and Dependabot continues to propose updates.

Dependency Review rejects newly introduced vulnerabilities at `moderate` severity or higher.

The scheduled `Dependency Audit` workflow runs `pip-audit` against the local project every Monday. This complements pull-request dependency review by detecting advisories published after a dependency has already been merged.

Pull-request validation workflows require only `contents: read` and do not receive write permissions.

## Main branch protection

After the new contexts have successfully appeared on a pull request, `main` should require these stable checks:

- `ci-gate`
- `windows-quality`
- `action-smoke`
- `pr-policy`
- `dependency-review`
- `CodeQL`

Keep strict up-to-date status checks, linear history, conversation resolution, administrator enforcement, no force pushes, and no branch deletion enabled.

Do not switch branch protection to a new context name before that context has completed successfully on a real pull request.
