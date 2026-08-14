# Changelog

## Unreleased

## 0.3.3 - 2026-08-13

### Fixed
- added a deterministic AI-draft fidelity guard that blocks high-confidence invented numeric literals, unsupported contradiction-resolution claims, unsupported strong requirements, and new out-of-scope constraints
- exposed `draft_fidelity` through REST and CLI while preserving deterministic-only exit semantics
- disabled Web UI `Use as input` for `UNSAFE` drafts while keeping copy/review available
- added regression coverage from the real qwen3:8b acceptance failure that invented 10,000/30,000 row thresholds and falsely declared the 2s/30s contradiction resolved

## 0.3.2 - 2026-08-13

### Fixed
- made improved-spec drafting gate-aware by supplying deterministic SG findings as structured provider context
- restored missing required sections conservatively through explicit TODO/open-question guidance instead of silently dropping them
- automatically rechecked generated drafts with the same deterministic core/configuration and exposed original-to-draft quality in REST, CLI, and Web UI

## 0.3.1 - 2026-08-12

### Fixed
- made CLI stdout encoding-safe on Windows console encodings such as `cp1251`, preserving valid JSON by escaping only characters the active stream cannot encode
- added regression coverage for Unicode AI output and Unicode source paths under a simulated `cp1251` stdout
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
