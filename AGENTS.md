# AGENTS.md

## Product invariants

- Keep the deterministic core free of network and provider dependencies.
- Every rule requires positive and negative tests.
- Stable rule IDs are public API; do not reuse them or silently change their meaning.
- `main` must remain releasable.
- Use GitHub-hosted runners for untrusted public pull requests.

## Project map

- `src/specforge_gate/` — package and CLI implementation.
- `tests/` — unit and regression tests.
- `examples/` — representative valid and invalid specifications.
- `docs/` — configuration, product, architecture, and roadmap documentation.
- `.github/workflows/` — mandatory quality, security, Windows, and release automation.
- `scripts/` — canonical local bootstrap and verification commands.

## Canonical commands

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1
.\scripts\check.ps1
```

Linux and macOS:

```bash
bash scripts/bootstrap.sh
bash scripts/check.sh
```

Do not replace the canonical checks with partial ad hoc commands in pull-request evidence.

## Change workflow

1. Start user-visible or repository behavior changes with an Issue.
2. Define problem, scope, out-of-scope, and observable acceptance criteria.
3. Create a dedicated branch; never push directly to `main`.
4. Implement the smallest coherent change.
5. Add or update positive and negative tests.
6. Update user-facing and contributor documentation.
7. Run the canonical check script.
8. Open a PR that closes the Issue and records exact verification results.

## Compatibility rules

- Python 3.11 is the minimum supported runtime.
- Text, JSON, and Markdown output are public automation interfaces.
- Exit codes and stable rule IDs are compatibility-sensitive.
- Configuration changes must preserve clear validation errors without tracebacks.
- New dependencies require a documented reason and dependency-review approval.

## Documentation rules

Update the relevant files when behavior changes:

- `README.md` for installation, CLI, and contributor workflow;
- `docs/configuration.md` for configuration behavior;
- `docs/ROADMAP.md` for completed or rescheduled roadmap items;
- `CHANGELOG.md` for user-visible or repository-workflow changes.

## Release rules

- The version in `pyproject.toml` is the release source of truth.
- Release tags must be exactly `v<project.version>`.
- A release requires all Linux and Windows checks to pass.
- The tag workflow builds and validates both wheel and source distribution.
- Do not publish from an uncommitted local tree or bypass the tag workflow.
