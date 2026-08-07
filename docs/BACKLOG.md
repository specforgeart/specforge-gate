# Initial backlog

## Now

### 1. Project configuration

**Problem:** teams need different severities and exclusions.

**Scope:** load `.specgate.yml`, configure language, severity overrides, disabled rules, and excluded paths.

**Out of scope:** organization-level remote configuration.

**Acceptance criteria:**
- CLI automatically discovers `.specgate.yml` from the working directory.
- Invalid configuration returns exit code 2 and names the invalid field.
- A disabled rule produces no finding.
- A severity override is reflected in text, JSON, and Markdown reports.

### 2. Regression corpus

**Problem:** rule changes can silently increase false positives.

**Scope:** 40 annotated RU/EN examples with expected rule IDs.

**Out of scope:** machine-learning evaluation.

**Acceptance criteria:**
- At least 20 Russian and 20 English examples are stored under `examples/corpus`.
- Every example has an expected JSON result.
- CI fails when actual findings differ from the expected result.

### 3. REST API

**Status:** completed.

**Problem:** web and integration clients need the same engine through HTTP.

**Scope:** stateless FastAPI endpoint accepting text and returning the existing report schema.

**Out of scope:** authentication, history, database, and file storage.

**Acceptance criteria:**
- `POST /v1/check` accepts UTF-8 text up to the configured limit.
- Response uses the same schema as CLI JSON output.
- Input is not written to disk or logs.
- Health endpoint is available.

### 4. Minimal web UI

**Status:** completed.

**Problem:** non-CLI users need a zero-install demonstration.

**Scope:** paste text, run analysis, filter findings, copy Markdown report.

**Out of scope:** accounts, saved history, rich editor, and collaboration.

**Acceptance criteria:**
- `GET /` serves the browser UI from the optional API process without a frontend build step.
- Users can paste Markdown/plain text and run the existing `POST /v1/check` analysis.
- Findings can be filtered by error, warning, info, or all severities.
- The current deterministic report can be copied as Markdown.
- The page loads no external runtime assets and uses same-origin API requests only.
- Untrusted finding/report text is rendered through text nodes rather than HTML injection.
- The UI route stays outside the REST OpenAPI product contract.

### 5. Docker image and Compose

**Status:** completed.

**Problem:** users need a reproducible zero-setup way to run the REST API and web UI without managing a Python environment.

**Scope:** one hardened application image plus one-service Compose deployment for the existing API/UI process.

**Out of scope:** database, reverse proxy, TLS, authentication, orchestration, registry publishing, persistence, and AI/provider services.

**Acceptance criteria:**
- `docker compose up --build -d --wait` starts the existing API and web UI.
- `GET /healthz`, `GET /`, and `POST /v1/check` work from the running container.
- Default host publishing is loopback-only and can use a configurable local port.
- The application process runs as non-root.
- Compose uses a read-only root filesystem, ephemeral `/tmp`, dropped capabilities, and `no-new-privileges`.
- No host directory or persistent volume is mounted.
- Container smoke runs on GitHub-hosted Linux and is aggregated into the existing `ci-gate`.
- Existing deterministic core, REST schema, rule IDs, CLI behavior, and base runtime dependencies remain unchanged.

### 6. Reusable GitHub Action

**Status:** completed through Issue #15.

**Problem:** repositories need to stop low-quality specifications before merge.

**Scope:** check changed Markdown files and write a job summary.

**Out of scope:** Issue comments and external SaaS.

## Later

- Windows smoke workflow
- SARIF output
- GitHub PR comment
- optional Ollama/OpenAI-compatible analysis
