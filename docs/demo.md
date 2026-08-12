# Demo narrative

SpecForge Gate has two intentionally separate public demo paths:

1. a fast deterministic demo that requires no AI provider;
2. an optional end-to-end local AI demo using an explicitly configured Ollama instance.

The deterministic path remains the default product story because stable rule IDs and repeatable
findings are the quality gate. AI adds advisory contradiction analysis and conservative drafting
without changing deterministic results.

## Audience

The demo is for developers, analysts, product managers, team leads, and maintainers who prepare
implementation tasks for human developers or coding agents.

## Deterministic storyline

1. Start with a short task that looks actionable but lacks measurable delivery detail.
2. Run `specgate check examples/bad/export-task.md`.
3. Point to stable rule IDs such as `SG001`, `SG002`, and `SG003`.
4. Compare with `examples/improved/export-task.md`.
5. Re-run the check to demonstrate the improved path.
6. Optionally show `--format json` or `--format markdown`.

## Deterministic demo commands

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
specgate check examples/bad/export-task.md
specgate check examples/improved/export-task.md
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
specgate check .\examples\bad\export-task.md
specgate check .\examples\improved\export-task.md
```

## Optional local AI storyline

The complete local-provider demo is documented in
[End-to-end local AI demo](local-ai-demo.md). It uses the intentionally contradictory
`examples/ai/local-provider-demo.md` fixture.

With Ollama running and `qwen3:8b` installed:

```bash
python scripts/demo_local_ai.py --model qwen3:8b
```

The helper first runs the deterministic gate and then explicitly invokes `specgate ai-review`.
That separation is part of the product contract: AI is never automatic.

The same configured provider can then be demonstrated through the REST endpoint and same-origin Web
UI. The browser's **Analyze requirements** action remains deterministic while **AI Review** is a
separate explicit action.

## Regression evidence

`examples/corpus/` contains the deterministic 40-case manifest-driven regression corpus. The local
AI demo additionally has an automated loopback HTTP integration test that exercises the real
CLI/runtime/Ollama transport path without requiring a downloaded model in CI.

## What the demo must not imply

- AI findings are not deterministic SG rules.
- AI does not alter PASS/NEEDS WORK or stable rule IDs.
- A local model's wording is not a stable snapshot.
- The repository does not provide accounts, persistence, billing, RAG, Jira/Bitrix integration,
  automatic draft application, or provider routing/fallback.
- Do not use fake badges, screenshots, hosted endpoints, or synthetic testimonials.

## Current boundaries

- `specgate check` has no network or provider dependency.
- `specgate ai-review` accepts one explicit local file.
- AI provider configuration comes from process environment.
- Ollama defaults to loopback.
- Text, JSON, and Markdown outputs remain public interfaces.
- AI output is untrusted advisory content requiring human review.

## Related documentation

- [README](../README.md)
- [End-to-end local AI demo](local-ai-demo.md)
- [CLI AI review](cli-ai-review.md)
- [Web UI](web-ui.md)
- [REST API](rest-api.md)
- [Ollama adapter](ollama.md)
- [Product vision](product-vision.md)
- [Architecture](architecture.md)
- [Roadmap](ROADMAP.md)
