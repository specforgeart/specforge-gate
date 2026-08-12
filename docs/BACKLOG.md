# Backlog after v0.3.0

`v0.3.0` is the frozen first public alpha/MVP baseline. The earlier implementation backlog has been
absorbed into the completed roadmap. Items below are deferred ideas, not scheduled commitments.

## Deferred, not scheduled

- SARIF output
- optional GitHub pull-request comments
- accounts, saved history, and collaboration
- hosted/SaaS deployment concerns
- provider routing, fallback, retries, and backoff orchestration
- richer Markdown editing/rendering
- additional external integrations such as Jira or Bitrix

## Admission rule for new work

A new product slice starts only when at least one of these is true:

- users report a concrete recurring problem;
- an integration requires a clearly defined compatibility surface;
- quality/security/reliability evidence identifies a measurable gap;
- a release-blocking defect requires correction.

Every accepted item still follows the normal Issue -> branch -> canonical checks -> PR workflow.
The deterministic core, stable SG rule IDs, report formats, and exit semantics remain
compatibility-sensitive.
