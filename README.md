# SpecForge Gate

[![CI](https://github.com/specforgeart/specforge-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/ci.yml)
[![Windows Quality](https://github.com/specforgeart/specforge-gate/actions/workflows/windows-quality.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/windows-quality.yml)
[![Dependency Review](https://github.com/specforgeart/specforge-gate/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/dependency-review.yml)
[![PR Policy](https://github.com/specforgeart/specforge-gate/actions/workflows/pr-policy.yml/badge.svg)](https://github.com/specforgeart/specforge-gate/actions/workflows/pr-policy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Deterministic quality gate for requirements before humans or coding agents start building.**

SpecForge Gate (`specgate`) checks Markdown and text specifications for missing goals, expected results, testable acceptance criteria, scope boundaries, edge cases, vague wording, untestable criteria, and compound requirements. Its deterministic gate runs locally and offline, requires no API key, uploads no documents, and returns explainable findings with stable rule IDs. Optional AI review is a separate explicit action.

> Public alpha/MVP line: `v0.3.0`. Deterministic interfaces are compatibility-sensitive; optional AI remains advisory.

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
- **Local and offline by default:** `specgate check` reads local files/directories and performs no provider call.
- **No API key for deterministic use:** optional external AI providers may require operator-supplied credentials.
- **Automation-friendly:** text, JSON, and Markdown outputs are public interfaces.

Optional AI remains a separate explicit advisory layer exposed through the CLI, REST API, and Web UI; deterministic checks stay provider-free.

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

## Release status

`v0.3.0` is the first public alpha/MVP baseline; `v0.3.2` is the current patch release. Releases are distributed through GitHub Release assets (wheel, source distribution, and SHA-256 checksums); this release process does not publish to PyPI. See [Release process](docs/release.md).

## Current interfaces

| Interface | Status | Notes |
|---|---|---|
| CLI | available | `specgate check` stays deterministic; `specgate ai-review FILE` adds explicit advisory AI review. |
| JSON output | available | Use `--format json` for machine-readable automation. |
| Markdown output | available | Use `--format markdown` for reports and job summaries. |
| GitHub Action | available | Composite action checks changed Markdown files and writes a job summary. |
| REST API | available | Deterministic `POST /v1/check` plus explicit server-configured advisory `POST /v1/ai/review`. |
| AI review API | available | Combines the original deterministic report, validated contradictions, gate-aware improved draft, and automatic deterministic draft recheck. |
| Web UI | available | Same-origin deterministic checks plus explicit AI Review with provider status, contradictions, and improved draft. |
| Docker Compose | available | Hardened one-service local deployment for the existing API and UI. |
| AI provider contract | available | Standard-library-only adapter protocol for optional AI integrations. |
| Ollama adapter | available | Explicit synchronous adapter for Ollama `/api/chat`; selectable by CLI/API/Web UI AI review. |
| OpenAI-compatible adapter | available | Explicit synchronous Chat Completions adapter with optional caller-supplied Bearer auth. |
| Contradiction analysis | available | Advisory provider-neutral analysis with strict JSON and verbatim-source evidence validation. |
| Improved-spec draft | available | Advisory gate-aware Markdown drafting that consumes deterministic findings, preserves unresolved uncertainty, and is rechecked by the deterministic core. |

## Deterministic core vs optional AI

The deterministic core remains the authoritative quality gate: parser, rule engine, findings model, CLI, and text/JSON/Markdown reporters. It has no network dependency and no provider dependency.

The optional AI layer has a provider-neutral contract plus Ollama and OpenAI-compatible adapters. Provider network I/O occurs only when an adapter or advisory feature is explicitly invoked; deterministic checks remain provider-free. Advisory contradiction analysis validates model evidence against verbatim source substrings; improved-spec drafting is also available as a conservative human-reviewable Markdown draft that cannot change deterministic results. The REST API and CLI expose those two features through explicit provider-configured AI review flows, while `/v1/check` and `specgate check` remain deterministic-only. AI features must not change stable rule IDs, exit-code semantics, or deterministic report formats. See [CLI AI Review](docs/cli-ai-review.md), [REST API](docs/rest-api.md), [AI provider interface](docs/ai-provider-interface.md), [Ollama adapter](docs/ollama.md), [OpenAI-compatible adapter](docs/openai-compatible.md), [contradiction analysis](docs/contradiction-analysis.md), and [improved-spec draft](docs/improved-spec-draft.md).

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

## GitHub Action

The repository-root composite action checks changed Markdown files in pull requests without posting comments or sending specification content to an external service. It requires only `contents: read`.

```yaml
permissions:
  contents: read

jobs:
  requirements:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
        with:
          fetch-depth: 0

      - uses: specforgeart/specforge-gate@main
        with:
          fail-on: error
```

The development example uses `@main`; after `v0.3.0` is published, use the release tag or pin a reviewed commit SHA for stable automation. Empty `paths` selects added, modified, and renamed `.md` or `.markdown` files from the pull-request diff. Explicit paths, `fail-on`, and an explicit configuration path are also supported. See [GitHub Action](docs/github-action.md) and the [complete workflow example](.github/examples/specforge-gate.yml).

## REST API

Install the optional API dependencies and run the stateless service:

```bash
python -m pip install -e ".[api]"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Analyze inline text deterministically with `POST /v1/check`. Valid documents return HTTP `200` whether the deterministic report is `PASS` or `NEEDS WORK`; invalid request/configuration or suppression syntax returns HTTP `422`, and text above the configured limit returns HTTP `413`. The deterministic endpoint accepts no request-selected file path or URL and performs no outbound provider call. When server-side AI environment variables are configured, `GET /v1/ai/status` reports provider availability and `POST /v1/ai/review` explicitly runs deterministic analysis, contradiction analysis, gate-aware improved-spec drafting, and a deterministic recheck of the generated draft in one response. See [REST API](docs/rest-api.md).

## Web UI

The same optional API process serves a zero-install browser UI at `http://127.0.0.1:8000/`. Deterministic **Analyze requirements** remains a separate same-origin `/v1/check` action. When a server-side provider is configured, the page also exposes an explicit **AI Review** action backed by `/v1/ai/status` and `/v1/ai/review`, showing contradictions and a reviewable improved-spec draft with copy/use controls. The page loads no CDN assets and never accepts provider credentials in browser fields. See [Web UI](docs/web-ui.md).

## Docker Compose

Run the same REST API and web UI in one hardened local container:

```bash
docker compose up --build -d --wait
```

The default mapping is `127.0.0.1:8000:8000`; set `SPECFORGE_PORT` to choose another local port. The service runs non-root with a read-only root filesystem, ephemeral `/tmp`, dropped Linux capabilities, and `no-new-privileges`. No database, volume, reverse proxy, authentication, or AI provider is added. See [Docker image and Compose](docs/container.md).

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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
specgate check .\examples\bad\export-task.md
specgate check .\examples\improved\export-task.md
specgate check .\examples\bad\export-task.md --format json
specgate check .\examples\bad\export-task.md --format markdown
```

By default the CLI exits with code `1` when at least one error exists. Use `--fail-on warning` for a stricter gate or `--fail-on none` for report-only mode.

## CLI AI Review

`specgate ai-review FILE` runs the same deterministic report first, then explicitly requests contradiction analysis and a conservative improved draft from the provider configured in environment variables. It accepts one explicit file to prevent accidental bulk provider egress. Use `--format json` for the REST-compatible result shape or `--fail-on none` for advisory-only use. See [CLI AI Review](docs/cli-ai-review.md).

## Local Ollama demo

With Ollama running and `qwen3:8b` installed, run:

```bash
python scripts/demo_local_ai.py --model qwen3:8b
```

The helper checks the local model list, runs the deterministic gate, and then invokes the explicit advisory AI review against `examples/ai/local-provider-demo.md`. See [End-to-end local AI demo](docs/local-ai-demo.md).

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

- [Release process](docs/release.md) — version invariants, tag workflow, assets, and failure handling.
- [Product vision](docs/product-vision.md) — public product concept, audience, principles, and boundaries.
- [Demo narrative](docs/demo.md) — deterministic-first public demo and optional AI storyline.
- [End-to-end local AI demo](docs/local-ai-demo.md) — Ollama setup, CLI/API/Web UI operator flow, troubleshooting, and privacy boundary.
- [Architecture](docs/architecture.md) — public architecture overview and interface boundaries.
- [GitHub Action](docs/github-action.md) — pull-request selection, inputs, outputs, job summaries, and security boundary.
- [REST API](docs/rest-api.md) — stateless endpoint contract, optional installation, configuration, and security boundary.
- [Web UI](docs/web-ui.md) — zero-install paste-and-check demo, filtering, Markdown copy, and browser security boundary.
- [CLI AI Review](docs/cli-ai-review.md) — explicit one-file AI review, provider configuration, output contract, exit codes, and security boundary.
- [Docker image and Compose](docs/container.md) — hardened local container deployment and security boundary.
- [AI provider interface](docs/ai-provider-interface.md) — provider-neutral optional-AI contracts and boundaries.
- [Ollama adapter](docs/ollama.md) — local Ollama transport, configuration, errors, and security boundary.
- [OpenAI-compatible adapter](docs/openai-compatible.md) — Chat Completions transport, optional Bearer authentication, errors, and security boundary.
- [Contradiction analysis](docs/contradiction-analysis.md) — advisory AI contradiction contract, source-evidence validation, and deterministic boundary.
- [Improved-spec draft](docs/improved-spec-draft.md) — conservative advisory Markdown drafting, uncertainty handling, and provider boundary.
- [Quality gates](docs/quality-gates.md) — required merge checks, branch coverage, CI aggregation, and supply-chain controls.
- [Deep quality testing](docs/mutation-testing.md) — Hypothesis invariants, mutation-testing workflow, scope, and baseline process.
- [Configuration](docs/configuration.md) — `.specgate.yml` discovery, schema, severity overrides, and excludes.
- [Inline rule suppression](docs/suppression.md) — suppression directive syntax and validation behavior.
- [Roadmap](docs/ROADMAP.md) — deterministic-first roadmap and planned work.
- [Contributing](CONTRIBUTING.md) — issue-first contribution workflow and compatibility rules.
- [Security](SECURITY.md) — responsible vulnerability reporting for the public alpha.
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

The bootstrap scripts create `.venv`, install the project with development dependencies, and install the local pre-commit hook. The check scripts run Ruff, strict MyPy, tests with line and branch coverage at an enforced 85% floor, package build, Twine validation, and clean installed-wheel CLI, REST API, and web-UI route smoke tests.

Pull requests are verified on GitHub-hosted Linux and Windows runners. The Linux workflow runs static/package verification once, tests Python 3.11–3.13 separately, and exposes a stable `ci-gate`; the reusable Action exposes a stable `action-smoke` integration gate. See [`docs/quality-gates.md`](docs/quality-gates.md).

## Releases

`v0.3.0` is the first public alpha/MVP. Release publication is tag-driven: the tag must match `project.version` and point to a commit reachable from `main`. The Release workflow reruns canonical Linux checks, builds the wheel and source distribution, creates `SHA256SUMS`, and publishes the GitHub Release assets. PyPI publication is intentionally not part of this release. See [Release process](docs/release.md).

## License

MIT
