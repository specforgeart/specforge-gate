# Public demo narrative

SpecForge Gate is a deterministic quality gate for Markdown tasks and software requirements. The public demo story is intentionally CLI-first for v0.1.0: users run the local `specgate` command against an example task, inspect explainable rule IDs, and compare the result with an improved specification.

## Audience

The demo is for developers, analysts, product managers, team leads, and maintainers who prepare implementation tasks for human developers or coding agents.

## Narrative

1. Start with a short task that looks actionable but lacks measurable delivery detail.
2. Run `specgate check examples/bad/export-task.md` to show that deterministic rules find missing goals, expected results, acceptance criteria, scope boundaries, and failure handling.
3. Open the generated findings and point to stable rule IDs such as `SG001`, `SG002`, and `SG003` as the public explanation layer.
4. Compare the bad example with `examples/improved/export-task.md` to show what a better task contains.
5. Re-run the check on the improved example to demonstrate the pass path.
6. Optionally show `--format json` or `--format markdown` for automation-friendly output.

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

## What the demo must not imply

The public demo must not imply that planned interfaces already exist. REST API, minimal web UI, Docker Compose, reusable GitHub Action, and optional AI provider analysis are planned roadmap items, not current v0.1.0 behavior.

The demo must also avoid fake badges, screenshots, GIFs, hosted endpoints, synthetic testimonials, or claims about integrations that are not implemented in this repository.

## Current boundaries

- The deterministic core has no network or provider dependency.
- The CLI accepts local Markdown or text files and directories.
- Text, JSON, and Markdown report formats are public automation interfaces.
- Exit codes are controlled by `--fail-on` and are compatibility-sensitive.
- Rule IDs are stable public API and must remain explainable in public material.

## Related documentation

- [README](../README.md) for installation and CLI usage.
- [Product brief](PRODUCT_BRIEF.md) for scope and product promise.
- [Roadmap](ROADMAP.md) for planned interfaces and future analysis work.
- [Configuration](configuration.md) for `.specgate.yml` behavior.
- [Inline rule suppression](suppression.md) for documented suppression directives.
