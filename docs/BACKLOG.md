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

**Problem:** non-CLI users need a zero-install demonstration.

**Scope:** paste text, run analysis, filter findings, copy Markdown report.

**Out of scope:** accounts, saved history, rich editor, and collaboration.

### 5. Reusable GitHub Action

**Status:** completed through Issue #15.

**Problem:** repositories need to stop low-quality specifications before merge.

**Scope:** check changed Markdown files and write a job summary.

**Out of scope:** Issue comments and external SaaS.

## Later

- Docker image and Compose
- Windows smoke workflow
- SARIF output
- GitHub PR comment
- optional Ollama/OpenAI-compatible analysis
