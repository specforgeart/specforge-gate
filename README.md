# SpecForge Gate

Deterministic quality gate for software requirements and AI coding tasks.

> Working name and pre-alpha implementation. The public repository name may change before release.

## Why

A detailed task can still omit the expected result, scope boundaries, testable acceptance criteria, failure behavior, or measurable thresholds. SpecForge Gate detects these gaps before a human or coding agent starts implementation.

- no API key
- no document upload
- explainable rule IDs
- CLI-first
- JSON and Markdown output for automation

## Current rules

| ID | Check | Severity |
|---|---|---|
| SG001 | Goal section exists | error |
| SG002 | Expected result exists | error |
| SG003 | Acceptance criteria exist | error |
| SG004 | Out-of-scope section exists | warning |
| SG005 | Errors and edge cases exist | warning |
| SG101 | Vague wording | warning |
| SG102 | Untestable acceptance criterion | error |
| SG103 | Compound requirement | info |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
specgate check examples/bad/export-task.md
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
specgate check .\examples\bad\export-task.md
```

Machine-readable output:

```bash
specgate check task.md --format json
specgate check docs/ specs/task.md --format json
specgate check task.md --format markdown > report.md
```

By default the CLI exits with code `1` when at least one error exists. Use `--fail-on warning` for a stricter gate or `--fail-on none` for report-only mode.

Inline suppression directives:

```markdown
<!-- specgate-ignore-file SG004 SG005 -->
<!-- specgate-ignore-next-line SG101 -->
```

Suppression directives must be standalone full-line HTML comments. `specgate-ignore-file` is allowed only in the document preamble, while `specgate-ignore-next-line` targets the next non-empty, non-directive physical line. Directive names and rule IDs are case-insensitive; IDs may be separated by spaces, commas, or both. Unknown IDs and malformed directives are validation errors: the CLI prints the source path and directive line, exits with code `2` even with `--fail-on none`, and emits no traceback. See [`docs/suppression.md`](docs/suppression.md).

Project configuration:

```yaml
version: 1
language: ru
rules:
  SG101:
    enabled: false
  SG004:
    severity: error
exclude:
  - docs/archive/**
  - "**/generated/**"
```

`specgate check` automatically discovers `.specgate.yml` from the current working directory upward. Use `--config path/to/.specgate.yml` to provide an explicit configuration path. Explicit files are always analyzed; `exclude` patterns apply only to files discovered while checking directories. Invalid configuration exits with code `2` and names the invalid field. See [`docs/configuration.md`](docs/configuration.md) and [`.specgate.example.yml`](.specgate.example.yml).

## Public demo

The v0.1.0 public demo is CLI-first: run SpecForge Gate on a weak task, review explainable rule IDs, compare it with an improved task, and optionally show JSON or Markdown output for automation. REST API, minimal web UI, Docker Compose, reusable GitHub Action, and optional AI provider analysis are planned, not current behavior. See [`docs/public-demo.md`](docs/public-demo.md).

## Example

Bad input:

```text
Make a convenient and fast export of the result.
```

Output:

```text
NEEDS WORK

Errors: 3
Warnings: 4
Info: 0
```

See [`examples/bad`](examples/bad) and [`examples/improved`](examples/improved).

## Development

Canonical Windows PowerShell workflow:

```powershell
.\scripts\bootstrap.ps1
.\scripts\check.ps1
```

Canonical Linux and macOS workflow:

```bash
bash scripts/bootstrap.sh
bash scripts/check.sh
```

The bootstrap scripts create `.venv`, install the project with development dependencies, and install the local pre-commit hook. The check scripts run Ruff, strict MyPy, tests with at least 85% coverage, package build, Twine validation, and a clean installed-wheel CLI smoke test.

Pull requests are verified on GitHub-hosted Linux and Windows runners.

## Releases

1. Update `project.version` in `pyproject.toml`.
2. Merge the release-ready change into `main`.
3. Create and push the matching tag, for example `v0.1.0a1`.
4. The release workflow validates the tag, runs the canonical checks, builds wheel and source distributions, and creates the GitHub Release.

Automatic PyPI publication is intentionally deferred.

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## License

MIT
