# Ollama adapter

SpecForge Gate provides an optional `OllamaProvider` implementation of the shared `AIProvider`
contract. Deterministic rules do not import it. The adapter is used only by explicit optional AI
surfaces such as `specgate ai-review` and the server-configured REST/Web UI AI review flow.

## Transport

The adapter sends a synchronous non-streaming:

```text
POST /api/chat
```

The default origin is:

```text
http://127.0.0.1:11434
```

`AIRequest.system_prompt` and `AIRequest.user_prompt` become `system` and `user` chat messages.
`AIResponseFormat.JSON` adds Ollama's `format: "json"` request option. Text mode omits `format`.
Streaming is always disabled so one request maps to one normalized `AIResponse`.

## Direct adapter example

```python
from specforge_gate.ai import AIRequest, OllamaProvider

provider = OllamaProvider(model="qwen3:8b")
response = provider.generate(
    AIRequest(
        system_prompt="Review the requirement carefully.",
        user_prompt="The export should be fast and convenient.",
    )
)
print(response.text)
```

Instantiating the adapter performs no network request. Network I/O begins only when `generate()` is
called.

## Product configuration

The CLI/API product surfaces use the shared runtime environment resolver:

```text
SPECFORGE_AI_PROVIDER=ollama
SPECFORGE_AI_MODEL=qwen3:8b
```

Optional variables:

```text
SPECFORGE_AI_BASE_URL=http://127.0.0.1:11434
SPECFORGE_AI_TIMEOUT_SECONDS=60
```

The adapter itself still does not read environment variables; the runtime resolver constructs it
from operator configuration.

## End-to-end local demo

See [End-to-end local AI demo](local-ai-demo.md). The repository provides:

```bash
python scripts/demo_local_ai.py --model qwen3:8b
```

The helper checks Ollama's `GET /api/tags`, runs the deterministic gate, and then explicitly invokes
`specgate ai-review`. The automated test suite also exercises the complete Ollama HTTP path against
a temporary loopback stub so CI does not require a real model download.

## Response and errors

Successful responses normalize to `AIResponse(text, provider="ollama", model=...)`.

Transport/provider failures map to the shared error contract:

- HTTP 401/403 -> `authentication`;
- HTTP 429 -> `rate_limited` and retryable;
- other HTTP 4xx -> `request_rejected`;
- HTTP 5xx -> `unavailable` and retryable;
- socket/request timeout -> `timeout` and retryable;
- connection failure -> `unavailable` and retryable;
- malformed, oversized, or structurally invalid response -> `invalid_response`.

Provider response bodies are not copied into exception messages.

## Security boundary

The default endpoint is loopback, but callers may explicitly configure another HTTP(S) origin.
Treat any non-loopback origin as a deliberate data-egress decision because prompts are sent to that
server.

The adapter:

- performs no request during construction;
- has no credential loader;
- does not persist or log prompts/responses;
- disables streaming;
- caps a response body at 4 MiB;
- exposes no filesystem or URL input from the specification itself.

Generic provider routing, fallback, retries/backoff orchestration, persistence, and automatic draft
application remain outside the adapter's scope.
