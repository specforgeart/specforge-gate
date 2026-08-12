# Demo narrative

SpecForge Gate is a deterministic quality gate for Markdown tasks and software requirements. The public demo is intentionally CLI-first for v0.1.0: users run the local `specgate` command against an example task, inspect explainable rule IDs, and compare the result with an improved specification.

## Audience

The demo is for developers, analysts, product managers, team leads, and maintainers who prepare implementation tasks for human developers or coding agents.

## Storyline

1. Start with a short task that looks actionable but lacks measurable delivery detail.
2. Run `specgate check examples/bad/export-task.md` to show that deterministic rules find missing goals, expected results, acceptance criteria, scope boundaries, and failure handling.
3. Point to stable rule IDs such as `SG001`, `SG002`, and `SG003` as the public explanation layer.
4. Compare the bad example with `examples/improved/export-task.md` to show what a better task contains.
5. Re-run the check on the improved example to demonstrate the pass path.
6. Optionally show `--format json` or `--format markdown` for automation-friendly output.

## Regression corpus

The two public demo files remain intentionally simple. Broader behavior is protected by the 40-case manifest-driven corpus under [`examples/corpus`](../examples/corpus), which covers English and Russian bad, improved, and boundary specifications. The corpus is regression evidence, not a replacement for the short before/after demo.

Developers can run it with:

```bash
python -m pytest tests/test_example_corpus.py
```

## Demo commands

Linux and macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
specgate check examples/bad/export-task.md
specgate check examples/improved/export-task.md
specgate check examples/bad/export-task.md --format json
specgate check examples/bad/export-task.md --format markdown
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
specgate check .\examples\bad\export-task.md
specgate check .\examples\improved\export-task.md
specgate check .\examples\bad\export-task.md --format json
specgate check .\examples\bad\export-task.md --format markdown
```

## Before and after script

Before:

```text
Make a convenient and fast export of the result.
```

Explain that the task is risky because it has no explicit goal, expected result, testable acceptance criteria, out-of-scope boundaries, or failure behavior.

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

## What the demo must not imply

The public demo must distinguish implemented interfaces from planned ones. The GitHub Action, stateless REST API, minimal web UI, Docker/Compose deployment, provider-neutral AI contract, Ollama and OpenAI-compatible adapters, and advisory contradiction analysis are available. Improved-spec drafting remains planned roadmap work, and the deterministic CLI demo must not imply that optional AI affects PASS/NEEDS WORK.

The demo must also avoid fake badges, screenshots, GIFs, hosted endpoints, synthetic testimonials, or claims about integrations that are not implemented in this repository.

## Current boundaries

- The deterministic core has no network or provider dependency.
- The CLI accepts local Markdown or text files and directories.
- Text, JSON, and Markdown report formats are public automation interfaces.
- Exit codes are controlled by `--fail-on` and are compatibility-sensitive.
- Rule IDs are stable public API and must remain explainable in public material.

## Related documentation

- [README](../README.md) for installation and CLI usage.
- [Product vision](product-vision.md) for public product positioning.
- [Product brief](PRODUCT_BRIEF.md) for the internal scope summary.
- [Architecture](architecture.md) for the public architecture overview.
- [Roadmap](ROADMAP.md) for planned interfaces and future analysis work.
- [Configuration](configuration.md) for `.specgate.yml` behavior.
- [Inline rule suppression](suppression.md) for documented suppression directives.
