# Optional AI provider interface

SpecForge Gate has a provider-neutral contract for future optional AI analysis. The contract is available, but no provider adapter or AI-powered product feature is enabled by this change.

## Boundary

The deterministic parser, rules, report model, CLI, GitHub Action, REST API, web UI, and container deployment continue to work without a provider, API key, network call, or AI dependency. The deterministic core does not import `specforge_gate.ai`.

The provider contract uses only the Python standard library. Base runtime dependencies remain unchanged.

## Public contract

`specforge_gate.ai` exports:

- `AIProvider` — runtime-checkable structural protocol for provider adapters;
- `AIRequest` — provider-neutral system prompt, user prompt, and response mode;
- `AIResponse` — normalized text plus provider/model identity;
- `AIResponseFormat` — `text` or `json`;
- `AIProviderError` and `AIProviderErrorCode` — normalized adapter failure categories.

An adapter implements `provider_id`, `model`, and `generate(request)`. Provider-specific configuration such as base URLs, API keys, HTTP headers, retry policy, and wire payloads belongs in the adapter implementation, not in `AIRequest`.

## Why `text` and `json`

Future improved-spec drafting naturally returns text. Future contradiction analysis needs a structured mode. Keeping these two response modes in the shared request contract avoids leaking Ollama- or OpenAI-specific payload fields into analysis code.

The interface does not promise JSON-schema enforcement yet. A future provider adapter may translate `AIResponseFormat.JSON` to the provider's supported JSON mode and must normalize unsupported or malformed responses through `AIProviderError`.

## Error contract

Provider adapters must map transport/provider failures into one of these public categories:

- `configuration` — invalid or incomplete adapter configuration;
- `authentication` — provider rejected configured credentials;
- `request_rejected` — provider rejected an otherwise well-formed request;
- `rate_limited` — provider asked the client to slow down;
- `unavailable` — provider endpoint/service cannot be used;
- `timeout` — request exceeded the adapter timeout;
- `invalid_response` — provider returned a response the adapter cannot normalize.

`AIProviderError.retryable` is adapter-supplied metadata for future orchestration. The contract does not implement retries itself.

## Not implemented yet

This interface does not add:

- Ollama HTTP integration;
- OpenAI-compatible HTTP integration;
- API-key loading;
- provider discovery or routing;
- CLI/API/UI AI controls;
- contradiction analysis;
- improved-spec drafting;
- retry/backoff orchestration;
- persistence or request logging.

Those remain separate roadmap items so provider transport code cannot silently become part of the deterministic core.
