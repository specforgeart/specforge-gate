# Web UI

SpecForge Gate includes a self-contained browser interface for deterministic requirements checks and explicit advisory AI review. The page is served by the existing optional FastAPI process and requires no separate frontend toolchain.

## Run

Install the optional API dependencies and start the service:

```bash
python -m pip install -e ".[api]"
python -m uvicorn specforge_gate.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in a browser.

The deterministic UI works without an AI provider. To enable the separate AI Review action, configure one supported provider through the server-side environment variables documented in [REST API](rest-api.md). Provider URLs, model names, and credentials are never accepted from browser request bodies.

## Deterministic flow

The existing deterministic path remains independent:

1. paste Markdown or plain text;
2. select **Analyze requirements** or press Ctrl+Enter / Command+Enter;
3. the browser sends the text only to same-origin `POST /v1/check`;
4. inspect PASS/NEEDS WORK, counts, stable rule IDs, and suggestions;
5. filter findings by severity or copy the deterministic report as Markdown.

This action never calls an AI provider, even when the server has AI configured.

## Explicit AI Review flow

On page load, the browser checks same-origin `GET /v1/ai/status`. If no provider is configured, **AI Review** stays disabled and deterministic analysis remains fully usable. The status response exposes only availability, provider ID, and model; it never returns API keys.

When a provider is available, the user can explicitly select **AI Review**. The browser sends the current text to same-origin `POST /v1/ai/review`. The server then performs the existing deterministic analysis first and adds:

- validated direct contradictions with verbatim source evidence;
- a conservative improved-spec Markdown draft;
- provider/model identity for transparency.

The deterministic report returned by AI Review is rendered in the same findings panel. Contradictions and the improved draft are shown in a separate advisory section. AI output never changes stable SG rule IDs, deterministic findings, PASS/NEEDS WORK, or CLI exit semantics.

The draft can be copied to the clipboard or explicitly loaded back into the editor with **Use as input**. Loading the draft clears previous results and does not automatically rerun either deterministic or AI analysis, so the user retains control and can review the text before checking it again.

## Architecture

There is no React/Vite/npm build and no second application server. `GET /` returns one self-contained HTML/CSS/JavaScript document. Browser calls use only relative same-origin URLs:

- `POST /v1/check` for deterministic analysis;
- `GET /v1/ai/status` for non-secret provider availability;
- `POST /v1/ai/review` for explicit advisory AI review.

The `/` route remains excluded from OpenAPI. The four REST product paths are `/healthz`, `/v1/check`, `/v1/ai/status`, and `/v1/ai/review`.

## Security and privacy boundary

The UI:

- loads no CDN, font, image, stylesheet, or JavaScript runtime from another origin;
- uses only same-origin API calls;
- never accepts or stores provider URLs, model configuration, or API keys in browser fields;
- invokes AI only after an explicit user action;
- creates result elements with DOM APIs and assigns server-provided strings through `textContent`, never `innerHTML`;
- sets `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and `X-Content-Type-Options: nosniff`;
- uses a Content Security Policy restricting connections to the same origin and blocking objects, framing, forms, external fonts, and images;
- does not persist uploaded text, AI prompts, contradictions, or drafts.

AI Review can send the supplied specification from the server to the configured provider. Keep the default loopback bind for local demos. Authentication, TLS termination, rate limiting, and external exposure policy remain deployment concerns for this pre-release service.

## Out of scope

Accounts, saved history, collaboration, uploads, browser-side provider credential/configuration editing, automatic draft application, retry/routing orchestration, and rich Markdown rendering remain out of scope.

## Container deployment

The same browser UI is available from the one-service Docker/Compose deployment. Deterministic analysis remains provider-free. AI Review is available only when the container receives an explicit supported server-side provider configuration. See [Docker image and Compose](container.md).
