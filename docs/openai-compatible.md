# OpenAI-compatible adapter

SpecForge Gate provides an optional `OpenAICompatibleProvider` implementation of the shared
`AIProvider` contract. Deterministic rules do not import it. Explicit optional product surfaces
(`specgate ai-review` and server-configured REST/Web UI AI review) can select it through the shared
runtime environment configuration.

## Transport

The adapter sends a synchronous non-streaming request to:

```text
<base_url>/chat/completions
```

Callers provide the API root explicitly. A local compatible server may use an origin such as
`http://127.0.0.1:1234/v1`.

`AIRequest.system_prompt` and `AIRequest.user_prompt` become `system` and `user` chat messages.
`AIResponseFormat.JSON` adds:

```json
{"response_format":{"type":"json_object"}}
```

Streaming is disabled so one provider-neutral request maps to one normalized `AIResponse`.

## Authentication

`api_key` is optional because some local OpenAI-compatible servers do not require authentication.
When supplied, the adapter sends it only as:

```text
Authorization: Bearer <api_key>
```

The adapter does not read environment variables, configuration files, keyrings, or other secret
stores. The runtime resolver may obtain `SPECFORGE_AI_API_KEY` from process environment and pass it
to the adapter. The key is not returned in normalized product output.

## Direct adapter example

```python
import os

from specforge_gate.ai import AIRequest, OpenAICompatibleProvider

provider = OpenAICompatibleProvider(
    model="example-model",
    base_url=os.environ["COMPATIBLE_API_ROOT"],
    api_key=os.environ.get("COMPATIBLE_API_KEY"),
)
response = provider.generate(
    AIRequest(
        system_prompt="Review the requirement carefully.",
        user_prompt="The export should be fast and convenient.",
    )
)
print(response.text)
```

Instantiating the adapter performs no network call. `generate()` is the explicit outbound network
boundary.

## Product configuration

For CLI/API/Web UI AI review:

```text
SPECFORGE_AI_PROVIDER=openai-compatible
SPECFORGE_AI_MODEL=example-model
SPECFORGE_AI_BASE_URL=http://127.0.0.1:1234/v1
```

Optional:

```text
SPECFORGE_AI_API_KEY=...
SPECFORGE_AI_TIMEOUT_SECONDS=60
```

## Response and errors

Successful Chat Completions responses normalize `choices[0].message.content` plus the response
`model` into `AIResponse(text, provider="openai-compatible", model=...)`.

Transport/provider failures map to the shared error contract:

- HTTP 401/403 -> `authentication`;
- HTTP 408 -> `timeout` and retryable;
- HTTP 429 -> `rate_limited` and retryable;
- other HTTP 4xx -> `request_rejected`;
- HTTP 5xx and other endpoint failures -> `unavailable` and retryable;
- local/request timeout -> `timeout` and retryable;
- malformed, oversized, or structurally invalid response -> `invalid_response`.

Provider response bodies are not copied into normalized exception messages.

## Security boundary

Every configured non-local endpoint is a deliberate data-egress decision because system and user
prompts are sent to that server.

The adapter:

- requires the endpoint root to be supplied explicitly;
- performs no request during construction;
- does not persist or log prompts, responses, or API keys;
- disables streaming;
- caps a response body at 4 MiB;
- exposes no filesystem or URL input from the specification itself;
- keeps provider transport code outside the deterministic core.

Provider routing, fallback, retries/backoff orchestration, persistence, and automatic draft
application remain outside the adapter's scope.
