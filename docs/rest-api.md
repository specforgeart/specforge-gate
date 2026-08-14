# REST API

SpecForge Gate exposes an optional stateless HTTP interface over the same deterministic core used by the CLI and GitHub Action. FastAPI and Uvicorn remain optional `api` extra dependencies. The deterministic `POST /v1/check` path never invokes an AI provider.

The same process can now expose an explicit advisory AI review path when a provider is configured server-side. AI remains optional: leaving `SPECFORGE_AI_PROVIDER` unset keeps the deterministic API fully functional and makes the AI status endpoint report disabled.

## Install and run

```bash
python -m pip install -e ".[api]"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Use `0.0.0.0` only when you intentionally want the process reachable from other hosts. Authentication, TLS termination, rate limiting, and reverse-proxy policy are deployment concerns and are not implemented by the pre-release API server.

The same process serves the browser UI at `GET /`. The UI keeps deterministic `/v1/check` separate and enables explicit `/v1/ai/review` only when a server-side provider is configured.

## Endpoints

### `GET /healthz`

Returns process-level service/version metadata:

```json
{
  "status": "ok",
  "service": "specforge-gate",
  "version": "0.3.0"
}
```

### `POST /v1/check`

Analyzes one inline Markdown/text document. It never accepts a filesystem path or URL and never calls an AI provider.

```json
{
  "text": "# Goal\nShip export.\n\n# Expected result\nCSV export.\n\n# Acceptance criteria\n- Given data, when export runs, then CSV is returned.\n\n# Out of scope\n- PDF.\n\n# Errors and edge cases\n- Empty data.",
  "source": "ticket-123.md",
  "config": {
    "version": 1,
    "language": "en",
    "rules": {
      "SG004": {"enabled": false},
      "SG101": {"severity": "error"}
    }
  }
}
```

`source` is an opaque response label, not a path to open. If omitted it is `<api>`. `text` is limited to 1,000,000 characters by the default app configuration and `source` to 1,024 characters. Embedders can call `create_app(max_text_chars=...)` to set a different positive limit.

The response is the existing `AnalysisReport.to_dict()` contract. Findings do not change the HTTP status: a valid analyzed document returns HTTP `200` whether its report is `PASS` or `NEEDS WORK`. HTTP `422` is reserved for invalid request/configuration data and invalid suppression directives. Text above the configured limit returns HTTP `413`.

### `GET /v1/ai/status`

Reports whether this API process has an advisory provider configured. It exposes only provider/model identity and never returns API keys or other credentials.

Disabled response:

```json
{
  "enabled": false,
  "provider": null,
  "model": null
}
```

Configured response:

```json
{
  "enabled": true,
  "provider": "ollama",
  "model": "qwen3:8b"
}
```

Provider construction performs no network request. Invalid server-side AI configuration is returned as HTTP `503` rather than silently disabling the feature.

### `POST /v1/ai/review`

Runs one explicit advisory review pipeline over inline text:

1. run the unchanged deterministic analysis;
2. invoke advisory contradiction analysis;
3. pass validated contradiction context plus deterministic findings into gate-aware improved-spec drafting;
4. run the generated draft through the same deterministic core and inline configuration;
5. return the original report, draft report, contradictions, and draft in one response.

The request shape is the same inline `text`, `source`, and deterministic inline `config` shape used by `/v1/check`. AI review text is capped at 200,000 characters because both AI features enforce that bound.

Example response shape:

```json
{
  "deterministic": {
    "source": "ticket-123.md",
    "status": "NEEDS WORK",
    "summary": {
      "errors": 1,
      "warnings": 2,
      "info": 0,
      "total": 3
    },
    "findings": []
  },
  "draft_deterministic": {
    "source": "ticket-123.md#improved-draft",
    "status": "PASS",
    "summary": {
      "errors": 0,
      "warnings": 0,
      "info": 0,
      "total": 0
    },
    "findings": []
  },
  "provider": "ollama",
  "model": "qwen3:8b",
  "contradictions": [],
  "improved_spec": "# Goal\n..."
}
```

The advisory result does not modify deterministic findings, `PASS/NEEDS WORK`, rule IDs, report shapes, or CLI exit semantics. Provider/feature failures are HTTP failures for this explicit AI endpoint only. Normalized provider timeouts map to `504`, unavailable/configuration failures to `503`, rate limiting to `429`, and invalid provider/model output to `502`.

## Server-side AI configuration

AI credentials and provider URLs are server configuration, never request fields. Supported variables:

| Variable | Required | Meaning |
|---|---|---|
| `SPECFORGE_AI_PROVIDER` | yes to enable AI | `ollama` or `openai-compatible` |
| `SPECFORGE_AI_MODEL` | yes when enabled | provider model identifier |
| `SPECFORGE_AI_BASE_URL` | OpenAI-compatible: yes; Ollama: optional | API root; Ollama defaults to `http://127.0.0.1:11434` |
| `SPECFORGE_AI_API_KEY` | optional | Bearer key for OpenAI-compatible endpoints only |
| `SPECFORGE_AI_TIMEOUT_SECONDS` | optional | positive finite timeout; default `60` |

Example local Ollama launch:

```bash
export SPECFORGE_AI_PROVIDER=ollama
export SPECFORGE_AI_MODEL=qwen3:8b
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Example PowerShell configuration:

```powershell
$env:SPECFORGE_AI_PROVIDER = "ollama"
$env:SPECFORGE_AI_MODEL = "qwen3:8b"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

OpenAI-compatible deployments additionally set an explicit `SPECFORGE_AI_BASE_URL`; `SPECFORGE_AI_API_KEY` is supplied only when that endpoint requires Bearer authentication. The API never returns the key in status or review responses.

For a complete local Ollama operator walkthrough, see [End-to-end local AI demo](local-ai-demo.md).

## Inline deterministic configuration

Both analysis endpoints accept deterministic `version`, `language`, and per-rule `enabled` / `severity` overrides. Filesystem-oriented `.specgate.yml` fields such as `exclude` are intentionally rejected because the API analyzes inline text only.

Unknown fields and unknown rule IDs are rejected instead of ignored. Stable rule IDs and finding/report fields remain compatibility-sensitive public interfaces.

## Security boundary

The deterministic `/v1/check` path remains local-core-only and performs no outbound provider request. `/v1/ai/review` is a separate explicit egress path: submitted specification text is sent to the configured provider for contradiction analysis and drafting.

The API layer:

- accepts inline text only;
- reads no request-selected local files or URLs;
- has no persistence or upload storage;
- keeps provider credentials server-side rather than accepting them from request bodies;
- never exposes `SPECFORGE_AI_API_KEY` through the status/review schemas;
- performs provider network I/O only for explicit `/v1/ai/review` calls;
- keeps deterministic result semantics independent from advisory AI success or failure.

The browser UI adds no external asset requests. Deterministic analysis posts only to same-origin `/v1/check`; explicit AI Review posts to same-origin `/v1/ai/review` after provider status is read from `/v1/ai/status`. Its response sets no-store, no-referrer, nosniff, and a restrictive Content Security Policy; returned strings are inserted through DOM text nodes rather than `innerHTML`.

Production deployment should place authentication, TLS, request-rate controls, and external exposure policy in an appropriate reverse proxy or hosting layer. Treat all improved-spec drafts as untrusted model output requiring human review.

## Container deployment

The same API/UI process can be run with the repository Docker image and `compose.yaml`. See [Docker image and Compose](container.md). Containerization does not add persistence/authentication; provider environment variables are an explicit deployment choice when AI review is enabled.

## Draft fidelity in AI review (v0.3.3)

`POST /v1/ai/review` now returns `draft_fidelity` next to `draft_deterministic`:

```json
{
  "draft_fidelity": {
    "status": "UNSAFE",
    "summary": {"total": 2},
    "findings": [
      {
        "code": "AIF001",
        "message": "Draft introduces a numeric literal that is absent from the source.",
        "suggestion": "Remove the new number or replace the unsupported detail with an explicit TODO.",
        "evidence": "10,000"
      }
    ]
  }
}
```

The fidelity guard is local and provider-free. It does not alter `deterministic`, `draft_deterministic`, SG rule IDs, or the deterministic `/v1/check` endpoint.
