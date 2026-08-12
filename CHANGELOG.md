# Changelog

## Unreleased

### Fixed
- aligned contradiction-analysis and improved-spec-draft documentation with the shipped v0.3.0 CLI, REST, and Web UI AI review surfaces

## 0.3.0 - 2026-08-12

### Added
- end-to-end local Ollama demo helper, fixture, automated transport test, and operator guidance
- explicit `specgate ai-review FILE` command with text, JSON, and Markdown output
- explicit same-origin Web UI AI Review with provider status, contradiction rendering, and copy/use improved-draft controls
- explicit REST AI review flow with server-side provider configuration and deterministic/contradiction/draft orchestration
- provider-neutral conservative improved-spec Markdown drafting with explicit uncertainty handling
- provider-neutral advisory contradiction analysis with verbatim-source evidence validation
- optional OpenAI-compatible Chat Completions adapter with explicit Bearer auth support
- optional Ollama adapter over the provider-neutral AI contract using non-streaming `/api/chat`
- provider-neutral standard-library AI adapter contract for future optional providers
- Docker image and hardened one-service Compose deployment for the existing REST API and web UI
- minimal same-origin web UI for paste-and-check analysis, severity filtering, and Markdown report copy
- optional stateless REST API over the deterministic analysis core
- deep deterministic quality layer with Hypothesis invariants and scheduled mutmut mutation testing
- measured mutation baseline with 98.18% kill rate and an exact reviewed survivor allowlist
- hardened merge gates with stable CI and Action Smoke contexts, branch coverage, SHA-pinned Actions, moderate dependency review, and scheduled dependency auditing
- reusable composite GitHub Action with pull-request file selection and job summaries
- 40-example English and Russian regression corpus with manifest-driven contract tests
- public README, demo, product vision, architecture, contributing, security, and support documentation entry points
- initial parser and deterministic rule engine
- eight built-in rules
- CLI with text, JSON, and Markdown reports
- GitHub-hosted CI matrix for Python 3.11–3.13
- initial examples, product brief, roadmap, and contribution templates
- cross-platform bootstrap and canonical quality-check scripts
- Windows quality workflow and tag-based GitHub Release automation
- local pre-commit quality gates and expanded AI-agent instructions

### Changed
- promoted the first complete public MVP to version `0.3.0`
- modernized package licensing to SPDX metadata and declared Python 3.13 support
- hardened tag releases by requiring the tagged commit to be reachable from `main`
- added SHA-256 checksum publication for wheel and source-distribution release assets
- froze unscheduled feature expansion behind explicit post-release user evidence
