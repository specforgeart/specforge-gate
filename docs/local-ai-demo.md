# End-to-end local AI demo

This demo proves the complete optional local-provider path without changing the deterministic gate:

```text
local Markdown file
    -> specgate check
    -> explicit specgate ai-review
    -> Ollama on loopback
    -> validated contradictions
    -> conservative improved-spec draft
```

`specgate check` remains provider-free. Only the explicit AI review step sends specification text to
the configured provider.

## Prerequisites

- Python 3.11 or newer;
- a repository checkout with development dependencies installed;
- Ollama installed and running locally;
- one local chat model.

The documented example uses `qwen3:8b`. Ollama's model library exposes this model, and the local API
lists installed models through `GET /api/tags`.

Pull the example model:

```bash
ollama pull qwen3:8b
```

If the local Ollama service is not already running, start it in a separate terminal:

```bash
ollama serve
```

The canonical endpoint is `http://127.0.0.1:11434`.

## Install SpecForge Gate

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[api]"
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[api]"
```

## One-command CLI demo

Run:

```bash
python scripts/demo_local_ai.py --model qwen3:8b
```

The script:

1. checks `GET /api/tags` on the configured Ollama origin;
2. refuses to continue if the requested model is not installed;
3. runs `specgate check` with `--fail-on none`;
4. runs explicit `specgate ai-review` against the same file;
5. prints contradictions and the conservative improved draft.

The demo specification is:

```text
examples/ai/local-provider-demo.md
```

It intentionally contains two incompatible completion limits so contradiction analysis has a clear
piece of source evidence to inspect. Model output is non-deterministic, so the operator should judge
the quality of the advisory explanation/draft rather than expect an exact sentence snapshot.

Useful options:

```bash
python scripts/demo_local_ai.py --model qwen3:8b --format json
python scripts/demo_local_ai.py --model qwen3:8b --format markdown
python scripts/demo_local_ai.py --base-url http://127.0.0.1:11434
```

## Direct CLI configuration

The same flow can be run without the helper script.

Linux/macOS:

```bash
export SPECFORGE_AI_PROVIDER=ollama
export SPECFORGE_AI_MODEL=qwen3:8b
specgate check examples/ai/local-provider-demo.md --fail-on none
specgate ai-review examples/ai/local-provider-demo.md --fail-on none
```

Windows PowerShell:

```powershell
$env:SPECFORGE_AI_PROVIDER = "ollama"
$env:SPECFORGE_AI_MODEL = "qwen3:8b"
specgate check .\examples\ai\local-provider-demo.md --fail-on none
specgate ai-review .\examples\ai\local-provider-demo.md --fail-on none
```

## REST API and Web UI

Use the same environment configuration, then start the API process:

```bash
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

The page should show the configured provider/model and enable the separate **AI Review** button.
**Analyze requirements** remains deterministic-only.

PowerShell REST smoke:

```powershell
$body = @{
    text = Get-Content .\examples\ai\local-provider-demo.md -Raw
    source = "local-provider-demo.md"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/v1/ai/review" `
    -ContentType "application/json" `
    -Body $body
```

## Expected evidence

A successful operator demo demonstrates all of these boundaries:

- deterministic `specgate check` works independently of AI results;
- provider selection comes from process environment, not document text;
- the explicit AI path uses local Ollama;
- contradiction evidence must be copied verbatim from the source;
- the improved specification is advisory Markdown for human review;
- AI output does not modify SG rule IDs, findings, PASS/NEEDS WORK, or deterministic exit semantics.

The repository also contains an automated end-to-end transport test using a temporary loopback HTTP
stub. That test exercises the real CLI -> runtime resolver -> `OllamaProvider` -> HTTP -> validated
AI review path without requiring Ollama or a model download in CI.

## Troubleshooting

`demo: Ollama is unavailable`:

- verify that Ollama is running;
- verify the origin, normally `http://127.0.0.1:11434`;
- retry `curl http://127.0.0.1:11434/api/tags` or the platform-equivalent HTTP request.

`demo: Ollama model is not installed`:

```bash
ollama pull qwen3:8b
```

Provider timeout:

```bash
python scripts/demo_local_ai.py --model qwen3:8b --timeout 120
```

A small/local model can return invalid JSON, weak contradiction evidence, or a draft that violates
the strict output contract. SpecForge Gate rejects invalid provider output instead of silently
accepting it. Try the request again or use another locally installed model.

## Container note

The canonical local-provider demo runs the SpecForge API and Ollama on the same host. Container-to-
host Ollama networking differs by platform and deployment configuration, so the one-service Compose
setup is not the canonical path for this demo. Configure a non-loopback provider origin only as an
explicit data-egress/networking decision.

## Security and privacy

The default demo endpoint is loopback. The helper script sends only the selected local specification
to the configured Ollama origin and does not persist prompts/responses. If `--base-url` points to a
different host, that becomes an explicit data-egress decision.

Treat all model output as untrusted advisory text requiring human review.
