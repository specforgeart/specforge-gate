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
- Planned API, UI, Docker, and GitHub Action work must be presented as planned until implemented.

## Current capability

SpecForge Gate currently provides a local CLI that analyzes Markdown and text files or directories. It reports findings through text, JSON, and Markdown output formats.

The current deterministic rule set checks for required sections, vague wording, untestable acceptance criteria, and compound requirements. See the rule table in the [README](../README.md#current-rules).

## Planned capability

The roadmap includes a larger regression corpus, planned reusable GitHub Action, planned REST API, planned web UI, planned Docker Compose, and planned optional AI analysis. These are not available in the current implementation.

## Relationship to the product brief

This file is the public product entry point. The older [product brief](PRODUCT_BRIEF.md) remains a compact scope summary for repository history and should not contradict this public vision.
