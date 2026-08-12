# Optional AI provider interface

SpecForge Gate has a provider-neutral contract for optional AI analysis. The contract, Ollama adapter, OpenAI-compatible adapter, and advisory contradiction-analysis feature are available. No deterministic product path invokes a provider.

## Boundary

The deterministic parser, rules, report model, CLI, GitHub Action, REST API, web UI, and container deployment continue to work without a provider, API key, network call, or AI dependency. The deterministic core does not import `specforge_gate.ai`.

The provider contract uses only the Python standard library. Base runtime dependencies remain unchanged.

## Public contract

`specforge_gate.ai` exports:

- `AIProvider` — runtime-checkable structural protocol for provider adapters;
- `AIRequest` — provider-neutral system prompt, user prompt, and response mode;
- `AIResponse` — normalized text plus provider/model identity;
- `AIResponseFormat` — `text` or `json`;
- `AIProviderError` and `AIProviderErrorCode` — normalized adapter failure categories;
- `OllamaProvider` — concrete adapter using non-streaming Ollama chat requests;
- `OpenAICompatibleProvider` — concrete adapter using non-streaming OpenAI-compatible Chat Completions;
- `analyze_contradictions` and its immutable result/error types — provider-neutral advisory contradiction analysis.

An adapter implements `provider_id`, `model`, and `generate(request)`. Provider-specific configuration such as base URLs, API keys, HTTP headers, retry policy, and wire payloads belongs in the adapter implementation, not in `AIRequest`.

## Why `text` and `json`

Improved-spec drafting naturally returns text. Contradiction analysis uses the structured JSON mode. Keeping both response modes in the shared request contract avoids leaking Ollama- or OpenAI-specific payload fields into analysis code.

The interface does not promise JSON-schema enforcement yet. Implemented adapters translate `AIResponseFormat.JSON` to their provider-supported JSON mode and normalize unsupported or malformed responses through `AIProviderError`.

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

## Implemented adapter

`OllamaProvider` maps `AIRequest` to Ollama `POST /api/chat`. `OpenAICompatibleProvider` maps the same contract to `<base_url>/chat/completions` with optional explicit Bearer authentication. Both disable streaming and normalize responses/errors back into the shared contract. See [`ollama.md`](ollama.md) and [`openai-compatible.md`](openai-compatible.md).

## Not implemented yet

The optional AI layer still does not add:

- automatic environment/config/keyring API-key loading;
- provider discovery or routing;
- CLI/API/UI AI controls;
- improved-spec drafting;
- retry/backoff orchestration;
- persistence or request logging.

Those remain separate roadmap items so optional AI behavior cannot silently become part of the deterministic core. See [`contradiction-analysis.md`](contradiction-analysis.md) for the implemented advisory feature boundary.
