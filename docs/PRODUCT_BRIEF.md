# Product brief

## Product name

SpecForge Gate (`specgate`).

## User

A developer, analyst, product manager, or team lead preparing Markdown tasks and specifications for
human developers or coding agents.

## Problem

A task can look detailed while still lacking an observable outcome, scope boundaries, testable
acceptance criteria, failure behavior, or dependencies. Humans and coding agents then implement
different interpretations.

## Promise

The deterministic gate finds high-risk gaps locally, offline, without an API key, and without
sending the specification to a provider. Optional AI review is a separate explicit advisory path
that may send the selected specification to an operator-configured provider.

## Current v0.3.0 scope

- Markdown and plain text
- deterministic rule engine with stable SG rule IDs
- CLI with text, JSON, and Markdown reports
- project configuration and suppression
- Russian and English wording rules
- reusable GitHub Action
- stateless REST API and same-origin web UI
- Docker Compose deployment
- provider-neutral optional-AI contract
- Ollama and OpenAI-compatible adapters
- advisory contradiction analysis
- conservative improved-spec drafting
- explicit REST, Web UI, and CLI AI review flows
- end-to-end local Ollama operator demo

## Out of scope

- authentication and accounts
- storage of user documents
- billing
- team workspaces
- RAG
- mandatory LLM calls
- Jira and Bitrix integrations
- automatic draft application
- provider fallback/routing

## Release posture

`v0.3.0` is the first public alpha/MVP. The deterministic interfaces remain
compatibility-sensitive. Optional AI output remains untrusted advisory content requiring human
review. New feature expansion is intentionally deferred until there is explicit post-release
evidence for it.

## Public vision and demo

The public product entry point is [`product-vision.md`](product-vision.md). The deterministic-first
demo narrative is [`demo.md`](demo.md), the local-provider operator flow is
[`local-ai-demo.md`](local-ai-demo.md), and release operations are documented in
[`release.md`](release.md).

## Status semantics

- `PASS`: no findings
- `NEEDS WORK`: at least one finding
- process exit code is controlled independently by `--fail-on`
