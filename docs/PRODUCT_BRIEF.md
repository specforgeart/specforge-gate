# Product brief

## Working name

SpecForge Gate (`specgate`). The name is provisional until public repository creation.

## User

A developer, analyst, product manager, or team lead preparing Markdown tasks and specifications for human developers or coding agents.

## Problem

A task can look detailed while still lacking an observable outcome, scope boundaries, testable acceptance criteria, failure behavior, or dependencies. Humans and coding agents then implement different interpretations.

## Promise

Find high-risk gaps before implementation begins, without requiring an API key or sending the specification to a third party.

## v0.1 scope

- Markdown and plain text
- deterministic rule engine
- CLI
- text, JSON, and Markdown reports
- Russian and English wording rules
- planned GitHub Actions integration
- planned minimal web UI and API
- planned Docker Compose

## Out of scope

- authentication and accounts
- storage of user documents
- billing
- team workspaces
- RAG
- mandatory LLM calls
- Jira and Bitrix integrations

## Public demo narrative

The public demo narrative is CLI-first for v0.1.0: run local checks on the bad and improved example tasks, show deterministic findings with stable rule IDs, and avoid implying that planned API, UI, Docker, GitHub Action, or AI-provider features already exist. See [`public-demo.md`](public-demo.md).

## Status semantics

- `PASS`: no findings
- `NEEDS WORK`: at least one finding
- process exit code is controlled independently by `--fail-on`
