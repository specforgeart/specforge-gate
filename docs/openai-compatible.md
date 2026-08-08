# OpenAI-compatible adapter

SpecForge Gate provides an optional `OpenAICompatibleProvider` implementation of the shared `AIProvider` contract. It is transport plumbing only: deterministic rules do not import it, and no CLI/API/web-UI feature invokes it yet.

## Transport

The adapter sends a synchronous non-streaming request to:

```text
<base_url>/chat/completions
```

Callers provide the API root explicitly. Typical examples are `https://api.openai.com/v1` for the OpenAI Chat Completions API or a local compatible server such as `http://127.0.0.1:1234/v1`.

`AIRequest.system_prompt` and `AIRequest.user_prompt` become `system` and `user` chat messages. `AIResponseFormat.JSON` adds:

```json
{"response_format":{"type":"json_object"}}
```

Streaming is disabled so one provider-neutral request maps to one normalized `AIResponse`.

## Authentication

`api_key` is optional because some local OpenAI-compatible servers do not require authentication. When supplied, the adapter sends it only as:

```text
Authorization: Bearer <api_key>
```

The adapter does not read environment variables, configuration files, keyrings, or other secret stores. The calling application is responsible for obtaining the secret safely and passing it to the adapter. The adapter never includes the key in normalized exception messages.

## Example

```python
import os

from specforge_gate.ai import AIRequest, OpenAICompatibleProvider

provider = OpenAICompatibleProvider(
    model="gpt-4.1",
    base_url="https://api.openai.com/v1",
    api_key=os.environ["OPENAI_API_KEY"],
)
response = provider.generate(
    AIRequest(
        system_prompt="Review the requirement carefully.",
        user_prompt="The export should be fast and convenient.",
    )
)
print(response.text)
```

Instantiating the adapter performs no network call. `generate()` is the explicit outbound network boundary.

## Configuration

`OpenAICompatibleProvider` accepts:

- `model` — required non-empty provider model identifier;
- `base_url` — required HTTP(S) API root with no embedded credentials, query, or fragment;
- `api_key` — optional Bearer token supplied explicitly by the caller;
- `timeout` — positive finite request timeout in seconds, default `60`.

A path prefix in `base_url` is allowed because OpenAI-compatible servers commonly expose an API root such as `/v1`.

## Response and errors

Successful Chat Completions responses normalize `choices[0].message.content` plus the response `model` into `AIResponse(text, provider="openai-compatible", model=...)`.

Transport/provider failures map to the shared error contract:

- HTTP 401/403 → `authentication`;
- HTTP 408 → `timeout` and retryable;
- HTTP 429 → `rate_limited` and retryable;
- other HTTP 4xx → `request_rejected`;
- HTTP 5xx and other endpoint failures → `unavailable` and retryable;
- local/request timeout → `timeout` and retryable;
- malformed, oversized, or structurally invalid response → `invalid_response`.

Provider response bodies are not copied into normalized exception messages.

## Security boundary

Every configured non-local endpoint is a deliberate data-egress decision because system and user prompts are sent to that server. The adapter:

- requires the endpoint root to be supplied explicitly;
- performs no request during construction;
- does not persist or log prompts, responses, or API keys;
- disables streaming;
- caps a response body at 4 MiB;
- exposes no filesystem or URL input from the specification itself;
- keeps all provider transport code outside the deterministic core.

## Still planned

- provider selection/configuration in CLI, API, or web UI;
- contradiction analysis;
- improved-spec drafting;
- orchestration, fallback, retries, and backoff.
