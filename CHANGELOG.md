# Changelog

## Unreleased

### Added
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
