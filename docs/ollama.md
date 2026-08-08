# Ollama adapter

SpecForge Gate provides an optional `OllamaProvider` implementation of the shared `AIProvider` contract. It is transport plumbing only: deterministic rules do not import it, and no CLI/API/web-UI feature invokes it yet.

## Transport

The adapter sends a synchronous non-streaming `POST /api/chat` request. The default origin is:

```text
http://127.0.0.1:11434
```

`AIRequest.system_prompt` and `AIRequest.user_prompt` become `system` and `user` chat messages. `AIResponseFormat.JSON` adds Ollama's `format: "json"` request option. Text mode omits `format`.

Streaming is always disabled in this adapter so one request maps to one normalized `AIResponse`.

## Example

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

This example performs network I/O only when `generate()` is called. Instantiating the adapter does not probe the endpoint.

## Configuration

`OllamaProvider` accepts:

- `model` — required non-empty Ollama model name;
- `base_url` — optional HTTP(S) origin, defaulting to loopback;
- `timeout` — positive request timeout in seconds, default `60`.

`base_url` must be an origin only. Embedded credentials, path components, query strings, and fragments are rejected. The adapter does not read environment variables or configuration files and does not load API keys.

## Response and errors

Successful responses normalize to `AIResponse(text, provider="ollama", model=...)`.

Transport/provider failures map to the shared error contract:

- HTTP 401/403 → `authentication`;
- HTTP 429 → `rate_limited` and retryable;
- other HTTP 4xx → `request_rejected`;
- HTTP 5xx → `unavailable` and retryable;
- socket/request timeout → `timeout` and retryable;
- connection failure → `unavailable` and retryable;
- malformed, oversized, or structurally invalid response → `invalid_response`.

Provider response bodies are not copied into exception messages.

## Security boundary

The default endpoint is loopback, but callers may explicitly configure another HTTP(S) origin. Treat any non-loopback origin as a deliberate data egress decision because prompts are sent to that server.

The adapter:

- performs no request during construction;
- has no credential loader;
- does not persist or log prompts/responses;
- disables streaming;
- caps a response body at 4 MiB;
- exposes no filesystem or URL input from the specification itself.

Authentication for direct Ollama cloud access and generic provider routing remain outside this adapter's current scope.

## Still planned

- OpenAI-compatible adapter;
- provider selection/configuration in CLI, API, or web UI;
- contradiction analysis;
- improved-spec drafting;
- orchestration, fallback, retries, and backoff.
