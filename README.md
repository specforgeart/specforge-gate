# SpecForge Gate

[![CI](https://github.com/specforgeart/specforge-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/ci.yml)
[![Windows Quality](https://github.com/specforgeart/specforge-gate/actions/workflows/windows-quality.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/windows-quality.yml)
[![Dependency Review](https://github.com/specforgeart/specforge-gate/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/dependency-review.yml)
[![PR Policy](https://github.com/specforgeart/specforge-gate/actions/workflows/pr-policy.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/pr-policy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Deterministic quality gate for requirements before humans or coding agents start building.**

SpecForge Gate (`specgate`) checks Markdown and text specifications for missing goals, expected results, testable acceptance criteria, scope boundaries, edge cases, vague wording, untestable criteria, and compound requirements. It runs locally and offline, requires no API key, uploads no documents, and returns explainable findings with stable rule IDs.

> Working name and pre-alpha implementation. The public repository name may change before release.

## Who it is for

- Developers and maintainers who want implementation tasks to be testable before work starts.
- Analysts and product managers who write requirements for delivery teams.
- Team leads reviewing specifications before assigning them to humans or coding agents.
- Automation owners who need JSON or Markdown reports in local scripts and CI pipelines.

## The problem it solves

A task can look detailed while still omitting the expected result, scope boundaries, measurable acceptance criteria, failure behavior, or explicit non-goals. Those gaps lead to rework because different people and agents implement different interpretations.

SpecForge Gate catches these gaps early with deterministic checks instead of relying on an opaque model response.

## Why deterministic-first

- **Repeatable:** the same input and configuration produce the same findings.
- **Explainable:** each finding points to a stable rule ID such as `SG001` or `SG102`.
- **Local and offline:** the current CLI reads local files and directories only.
- **No API key:** no provider account is required for current functionality.
- **Automation-friendly:** text, JSON, and Markdown outputs are public interfaces.

Optional AI analysis is planned for later releases, but it will remain separate from the deterministic core.

## 15-second example

```bash
specgate check examples/bad/export-task.md
```

Example result:

```text
NEEDS WORK

Errors: 3
Warnings: 4
Info: 0
```

## Before and after

Before:

```text
Make a convenient and fast export of the result.
```

Why it needs work:

- no explicit goal section;
- no observable expected result;
- no testable acceptance criteria;
- vague words such as “convenient” and “fast”.

After:

```markdown
# Goal

Allow an operator to export filtered order results to a CSV file.

# Expected result

The user receives a UTF-8 CSV file containing only orders that match the active filters.

# Acceptance criteria

- Given filtered order results, when the user selects Export CSV, then the downloaded file contains the same filtered rows.
- Given no matching orders, when the user selects Export CSV, then the system downloads a CSV file with headers and no data rows.
- Given an export failure, when the user retries, then the system shows a clear error message and does not create a partial file.

# Out of scope

- XLSX export
- scheduled exports
- emailing export files

# Errors and edge cases

- empty result sets
- export generation failure
- non-ASCII customer names
```

See the repository examples in [`examples/bad`](examples/bad) and [`examples/improved`](examples/improved).

## Current and planned interfaces

| Interface | Status | Notes |
|---|---|---|
| CLI | available | `specgate check` analyzes local Markdown/text files and directories. |
| JSON output | available | Use `--format json` for machine-readable automation. |
| Markdown output | available | Use `--format markdown` for reports and job summaries. |
| GitHub Action | planned | Planned reusable workflow integration; not implemented in this repository yet. |
| REST API | planned | Planned stateless interface; not implemented in this repository yet. |
| Web UI | planned | Planned paste-and-check demo; not implemented in this repository yet. |

Docker Compose and optional AI-provider analysis are also planned work, not current functionality.

## Deterministic core vs optional AI

The current product is the deterministic core: parser, rule engine, findings model, CLI, and text/JSON/Markdown reporters. It has no network dependency and no provider dependency.

A future optional AI layer may add contradiction analysis or improved-spec drafting, but planned AI features must not change stable rule IDs, exit-code semantics, or deterministic report formats.

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

## Regression corpus

`examples/corpus/` contains 40 manifest-driven English and Russian specifications: bad, improved, and boundary cases across ten product domains. The corpus fixes the expected status, rule IDs, severity, selected finding locations, and CLI exit behavior without snapshotting complete messages or reports.

Run the focused corpus suite after installing development dependencies:

```bash
python -m pytest tests/test_example_corpus.py
```

The canonical `scripts/check.ps1` and `scripts/check.sh` commands include the same tests.

## Quick start: Linux and macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
specgate check examples/bad/export-task.md
specgate check examples/improved/export-task.md
specgate check examples/bad/export-task.md --format json
specgate check examples/bad/export-task.md --format markdown
```

## Quick start: Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
specgate check .\examples\bad\export-task.md
specgate check .\examples\improved\export-task.md
specgate check .\examples\bad\export-task.md --format json
specgate check .\examples\bad\export-task.md --format markdown
```

By default the CLI exits with code `1` when at least one error exists. Use `--fail-on warning` for a stricter gate or `--fail-on none` for report-only mode.

## Configuration and suppression

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

## Documentation

- [Product vision](docs/product-vision.md) — public product concept, audience, principles, and boundaries.
- [Demo narrative](docs/demo.md) — CLI-first public demo script and demo guardrails.
- [Architecture](docs/architecture.md) — public architecture overview and planned-interface boundaries.
- [Configuration](docs/configuration.md) — `.specgate.yml` discovery, schema, severity overrides, and excludes.
- [Inline rule suppression](docs/suppression.md) — suppression directive syntax and validation behavior.
- [Roadmap](docs/ROADMAP.md) — deterministic-first roadmap and planned work.
- [Contributing](CONTRIBUTING.md) — issue-first contribution workflow and compatibility rules.
- [Security](SECURITY.md) — responsible vulnerability reporting for the pre-release project.
- [Support](SUPPORT.md) — where to ask questions, report bugs, and request features.

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

## License

MIT
