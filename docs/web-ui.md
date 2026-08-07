# Minimal web UI

SpecForge Gate includes a self-contained browser interface for non-CLI users who want to try the deterministic gate without installing a separate frontend toolchain.

## Run

Install the optional API dependencies and start the existing service:

```bash
python -m pip install -e ".[api]"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in a browser.

## Flow

The page supports the intentionally small backlog scope:

1. paste Markdown or plain text;
2. run the same deterministic analysis exposed by `POST /v1/check`;
3. inspect status and error/warning/info counts;
4. filter findings by severity;
5. copy the current report as Markdown.

A built-in example is available for demo use. The page also supports Ctrl+Enter (or Command+Enter) to run the check.

## Architecture

There is no React/Vite/npm build and no second application server. The optional FastAPI process serves a self-contained HTML/CSS/JavaScript document at `GET /`. Browser analysis calls use a relative `/v1/check` URL, so the same REST contract remains the single analysis path.

The `/` route is excluded from OpenAPI. The REST product contract remains `GET /healthz` and `POST /v1/check`.

## Security and privacy boundary

The UI:

- loads no CDN, font, image, stylesheet, or JavaScript runtime from another origin;
- sends pasted text only to same-origin `/v1/check`;
- creates result elements with DOM APIs and assigns server-provided strings through `textContent` rather than `innerHTML`;
- sets `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and `X-Content-Type-Options: nosniff`;
- sets a Content Security Policy that restricts connections to the same origin and blocks objects, framing, forms, external fonts, and images;
- inherits the REST boundary: no request-selected filesystem path/URL, persistence, upload storage, or AI/provider call.

The pre-release server still does not implement authentication, TLS termination, rate limiting, or deployment exposure policy. Keep the default loopback bind for local demos; production exposure requires an appropriate hosting/reverse-proxy layer.

## Out of scope

Accounts, saved history, a rich editor, collaboration, uploads, browser-side configuration editing, and AI-assisted rewriting are intentionally not part of this minimal UI.

## Container deployment

The same browser UI is available from the one-service Docker/Compose deployment. See [Docker image and Compose](container.md).
