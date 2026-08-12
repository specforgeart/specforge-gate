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
- Planned AI features must be optional and separate from deterministic checks.
- Available and planned interfaces must be labeled accurately; implemented API/UI/container surfaces must not be confused with planned AI work.

## Current capability

SpecForge Gate currently provides a local CLI, a reusable GitHub Action, an optional stateless REST API, a minimal same-origin web UI, a Docker/Compose deployment for that same API/UI process, an optional-AI provider contract with Ollama and OpenAI-compatible adapters, provider-neutral advisory contradiction analysis, and conservative improved-spec drafting. The REST API now has an explicit server-configured AI review path that combines the deterministic report, contradictions, and improved draft without changing deterministic semantics. The CLI analyzes Markdown and text files or directories. The Action checks pull-request Markdown changes or explicit paths and writes a Markdown job summary. The browser UI remains deterministic-only for now.

The current deterministic rule set checks for required sections, vague wording, untestable acceptance criteria, and compound requirements. See the rule table in the [README](../README.md#current-rules).

## Planned capability

The REST API, minimal web UI, Docker/Compose deployment, provider-neutral AI contract, Ollama adapter, OpenAI-compatible adapter, advisory contradiction analysis, conservative improved-spec drafting, and REST AI review flow are available around the deterministic core. Browser and CLI AI controls remain planned.

## Relationship to the product brief

This file is the public product entry point. The older [product brief](PRODUCT_BRIEF.md) remains a compact scope summary for repository history and should not contradict this public vision.
