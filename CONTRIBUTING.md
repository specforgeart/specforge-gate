# Contributing

Thank you for helping improve SpecForge Gate. The project is pre-release, but rule IDs, output formats, and exit-code behavior are treated as compatibility-sensitive because users may automate against them.

## Workflow

1. Start user-visible or repository-behavior changes with a GitHub Issue.
2. Define the problem, scope, out-of-scope items, and observable acceptance criteria.
3. Create a dedicated branch for the change.
4. Do not push directly to `main`.
5. Implement the smallest coherent change.
6. Add or update tests and documentation.
7. Run the canonical bootstrap and check commands.
8. Open a pull request that includes `Closes #...`.

## Tests for rules

Every rule change requires positive and negative coverage:

- positive tests for inputs that must produce the finding;
- negative tests for inputs that must not produce the finding;
- regression tests when fixing false positives or false negatives.

Do not reuse stable rule IDs for different meanings, and do not silently change rule semantics.

## Canonical local commands

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

Do not replace these commands with partial ad hoc checks in pull-request evidence.

## Pull requests

Pull requests should:

- use a focused branch, not `main`;
- include `Closes #...` in the description;
- follow [`.github/pull_request_template.md`](.github/pull_request_template.md);
- describe motivation, implementation, testing, risks, and limitations;
- include documentation updates for behavior or workflow changes;
- avoid unrelated refactoring;
- avoid new dependencies unless the reason is documented and dependency review is expected;
- avoid `Co-authored-by` trailers for people who did not contribute to the change.

## Pull-request quality gates

Pull requests must pass the stable merge gates documented in [`docs/quality-gates.md`](docs/quality-gates.md). Linux static/package work runs once, runtime tests cover Python 3.11–3.13, Windows runs the canonical scripts, the reusable Action has an integration smoke gate, dependency changes are reviewed, and CodeQL remains part of merge protection.

Do not weaken, rename, or remove a required status context without first introducing and observing its replacement on a real pull request. Third-party Actions in protected workflows must use reviewed full commit SHAs rather than movable tags.

## Compatibility-sensitive areas

Treat the following as public automation contracts:

- stable rule IDs and their meanings;
- text, JSON, and Markdown output formats;
- CLI arguments and package interfaces;
- exit-code behavior;
- configuration validation errors.

Changes to these areas require clear Issue scope, tests, documentation, and release-note attention.
