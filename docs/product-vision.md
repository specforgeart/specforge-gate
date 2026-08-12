# Product vision

SpecForge Gate helps teams improve software requirements before implementation starts. It is designed for Markdown tasks, product specifications, and AI coding prompts that need clear goals, expected results, acceptance criteria, scope boundaries, and failure behavior.

## Promise

Find high-risk requirement gaps locally, offline, and without an API key. Every finding should be deterministic, explainable, and suitable for automation.

## Audience

- Developers and maintainers preparing issues or pull-request tasks.
- Analysts and product managers writing implementation-ready specifications.
- Team leads reviewing work before assignment.
- Automation owners who need machine-readable quality reports.

## Product principles

- Deterministic checks come first.
- The core must remain free of network and provider dependencies.
- Stable rule IDs are public API.
- Text, JSON, and Markdown outputs are automation interfaces.
- AI features must remain optional and separate from deterministic checks.
- Available and deferred interfaces must be labeled accurately; implemented product surfaces must not be confused with unscheduled backlog ideas.

## Current capability

SpecForge Gate currently provides a local CLI, a reusable GitHub Action, an optional stateless REST API, a minimal same-origin web UI, a Docker/Compose deployment for that same API/UI process, an optional-AI provider contract with Ollama and OpenAI-compatible adapters, provider-neutral advisory contradiction analysis, and conservative improved-spec drafting. The REST API now has an explicit server-configured AI review path that combines the deterministic report, contradictions, and improved draft without changing deterministic semantics. The CLI keeps `specgate check` deterministic for files/directories and also exposes explicit one-file `specgate ai-review` for advisory contradictions and drafting. The Action checks pull-request Markdown changes or explicit paths and writes a Markdown job summary. The browser UI now keeps deterministic analysis separate while also exposing an explicit server-configured AI Review flow for contradiction analysis and conservative drafting.

The current deterministic rule set checks for required sections, vague wording, untestable acceptance criteria, and compound requirements. See the rule table in the [README](../README.md#current-rules).

## Release status

`v0.3.0` is the first public alpha/MVP. The REST API, web UI, Docker/Compose deployment, provider-neutral AI contract, Ollama/OpenAI-compatible adapters, advisory contradiction analysis, conservative improved-spec drafting, explicit REST/Web UI/CLI AI review, and the local-provider operator demo are available around the deterministic core. New product-surface work is intentionally deferred until post-release evidence justifies it.

## Relationship to the product brief

This file is the public product entry point. [The product brief](PRODUCT_BRIEF.md) is the compact current scope summary and should not contradict this public vision.
