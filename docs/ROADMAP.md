# Roadmap

## v0.1.0 — Deterministic quality gate

- [x] Repository scaffold
- [x] Lightweight Markdown parser
- [x] Finding and report model
- [x] First eight deterministic rules
- [x] CLI with text, JSON, and Markdown output
- [x] Linux CI on standard GitHub-hosted runners
- [x] Cross-platform developer scripts
- [x] Pre-commit hooks
- [x] Project configuration file
- [x] Rule suppression
- [x] Public README, demo, product vision, architecture, contributing, security, and support entry points
- [x] 40-example regression corpus
- [x] Windows installation smoke test
- [x] Release archive

## Planned interface expansion

- [x] Reusable GitHub Action
- [x] REST API
- [x] Minimal web UI
- [x] Docker image and Compose

## v0.2.0 — Optional AI analysis

- [x] Provider interface
- [x] Ollama integration
- [x] OpenAI-compatible endpoint
- [x] Contradiction analysis
- [x] Improved-spec draft

## v0.3.0 — AI product flow

- [x] Server-side AI provider configuration
- [x] REST AI review endpoint combining deterministic findings, contradictions, and improved draft
- [x] Web UI AI review flow
- [x] CLI AI review command
- [x] End-to-end local-provider demo and operator guidance

## Release posture

`v0.3.0` is the first public alpha/MVP release line. After publication, new product-surface work is
not started automatically. Deferred ideas remain in `BACKLOG.md` until an explicit Issue is backed
by user evidence, a concrete integration need, or a measured quality/reliability problem.
