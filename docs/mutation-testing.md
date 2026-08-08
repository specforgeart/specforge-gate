# Deep deterministic quality testing

SpecForge Gate uses two complementary test layers:

1. the required fast pull-request gate;
2. a deeper property-based and mutation-testing layer.

## Property-based tests

Hypothesis is a development-only dependency and runs inside the normal pytest suite on Python 3.11, 3.12, and 3.13. The property tests focus on invariants rather than additional example fixtures:

- repeated analysis of identical text/configuration is identical;
- LF, CRLF, and CR input normalize to the same analysis result;
- arbitrary Unicode input cannot produce unknown rule IDs or invalid severities;
- every reported line points to a real normalized document line;
- disabling a rule prevents findings from that rule;
- a severity override changes severity without changing finding identity/location;
- valid suppression directives cannot create semantic findings;
- JSON and Markdown reporters preserve report counts and contract data.

The current public `Finding` location contract is line-based; there is no public column field. Deep-quality tests therefore validate every location field that currently exists without adding a new public API as part of Issue #19.

Hypothesis keeps its normal local example database under `.hypothesis/`. On CI, Hypothesis' CI profile is deterministic and prints reproduction data for failures.

## Mutation testing

Mutation testing uses mutmut 3.7.0 on Ubuntu. It intentionally does not run in the required pull-request gate because mutmut is substantially more expensive than pytest and requires POSIX `fork` support.

Permanent triggers after the Issue #19 bootstrap are:

- weekly schedule;
- manual `workflow_dispatch`.

The workflow has `contents: read` permissions only.

`pyproject.toml` limits mutation to meaningful deterministic product logic and excludes package metadata, CLI argument plumbing, REST API/web-UI interface plumbing, GitHub Action integration plumbing, and optional AI provider/interface plumbing, including the Ollama transport adapter. Provider adapters and AI analysis do not participate in the historical deterministic mutation baseline. `scripts/mutation_summary.py` reads mutmut 3.x `.meta` files and writes a non-interactive summary to the job summary and logs.

The measured baseline has nine reviewed equivalent/platform-equivalent survivors. Their exact IDs live in `.github/mutation-allowed-survivors.txt`. The summary script fails a scheduled/manual mutation run if any survivor appears outside that allowlist; accepted survivors that become killed do not fail the run.

See [`mutation-baseline.md`](mutation-baseline.md) for the measured baseline and survivor triage.

## Native Windows

The canonical Windows QA continues to run all Hypothesis tests through pytest. mutmut itself is not executed natively on Windows because mutmut 3.x requires `fork`; use the GitHub-hosted Ubuntu workflow (or WSL for local experiments) instead.
