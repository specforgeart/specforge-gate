# REST API

SpecForge Gate exposes an optional stateless HTTP interface over the same deterministic core used by the CLI and GitHub Action. The API does not add network or provider dependencies to the core package: FastAPI and Uvicorn are installed only through the `api` extra.

## Install and run

```bash
python -m pip install -e ".[api]"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Use `0.0.0.0` only when you intentionally want the process reachable from other hosts. Authentication, TLS termination, rate limiting, and reverse-proxy policy are deployment concerns and are not implemented by the pre-release API server.

The same process serves the minimal browser UI at `GET /`. That page is intentionally excluded from OpenAPI because `/healthz` and `/v1/check` remain the REST product contract.

## Endpoints

### `GET /healthz`

Returns process-level service/version metadata:

```json
{
  "status": "ok",
  "service": "specforge-gate",
  "version": "0.1.0a1"
}
```

### `POST /v1/check`

Analyzes one inline Markdown/text document. It never accepts a filesystem path or URL.

```json
{
  "text": "# Goal\nShip export.\n\n# Expected result\nCSV export.\n\n# Acceptance criteria\n- Given data, when export runs, then CSV is returned.\n\n# Out of scope\n- PDF.\n\n# Errors and edge cases\n- Empty data.",
  "source": "ticket-123.md",
  "config": {
    "version": 1,
    "language": "en",
    "rules": {
      "SG004": {"enabled": false},
      "SG101": {"severity": "error"}
    }
  }
}
```

`source` is an opaque response label, not a path to open. If omitted it is `<api>`. `text` is limited to 1,000,000 characters by the default app configuration and `source` to 1,024 characters. Embedders can call `create_app(max_text_chars=...)` to set a different positive limit.

The response is the existing `AnalysisReport.to_dict()` contract:

```json
{
  "source": "ticket-123.md",
  "status": "PASS",
  "summary": {
    "errors": 0,
    "warnings": 0,
    "info": 0,
    "total": 0
  },
  "findings": []
}
```

Findings do not change the HTTP status: a valid analyzed document returns HTTP `200` whether its report is `PASS` or `NEEDS WORK`. HTTP `422` is reserved for invalid request/configuration data and invalid suppression directives. Text above the configured limit returns HTTP `413`.

## Inline configuration

The API supports `version`, `language`, and per-rule `enabled` / `severity` overrides. Filesystem-oriented `.specgate.yml` fields such as `exclude` are intentionally rejected because the API analyzes inline text only.

Unknown fields and unknown rule IDs are rejected instead of ignored. Stable rule IDs and finding/report fields remain compatibility-sensitive public interfaces.

## Security boundary

The API layer:

- accepts inline text only;
- performs no outbound network calls;
- reads no request-selected local files;
- has no persistence, upload, authentication, CORS policy, or provider integration;
- calls the same deterministic `analyze_text()` core as the CLI.

The browser UI adds no external asset requests and posts analysis only to same-origin `/v1/check`. Its response sets no-store, no-referrer, nosniff, and a restrictive Content Security Policy; returned finding data is inserted through DOM text nodes rather than `innerHTML`.

Production deployment should place authentication, TLS, request-rate controls, and external exposure policy in an appropriate reverse proxy or hosting layer.
