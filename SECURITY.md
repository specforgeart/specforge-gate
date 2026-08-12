# Security policy

SpecForge Gate is a pre-release project. Security reports are welcome, but there is no promised service-level agreement or guaranteed response time.

## Supported state

The active `main` branch and open release-preparation work are the supported security review targets. Older commits, local forks, and unpublished experiments are not supported as maintained release lines.

## What to report

Please report suspected vulnerabilities such as:

- unsafe handling of local files or paths;
- command execution risks;
- dependency-related vulnerabilities;
- workflow or release-process weaknesses;
- disclosure of sensitive data through logs or reports.

## How to report

Do not publicly disclose a suspected vulnerability before it has been reviewed.

If GitHub private vulnerability reporting is available for this repository, use it. If it is not available, open a GitHub Issue with a minimal, non-exploitative description and ask for a maintainer-preferred private follow-up path. Do not include exploit details, secrets, tokens, or sensitive files in a public Issue.

## Scope boundaries

The deterministic CLI and GitHub Action do not require an API key or upload documents. The optional REST API is stateless and does not persist request bodies. Its deterministic `/v1/check` path performs no provider call. AI provider egress is isolated behind explicit `/v1/ai/review` requests and server-side environment configuration; provider URLs and credentials are never accepted from request bodies, and `/v1/ai/status` never exposes API keys. The web UI is served from the same API process, loads no external runtime assets, keeps deterministic `/v1/check` separate, and invokes same-origin `/v1/ai/review` only after an explicit user action when a server-side provider is configured. Provider credentials are never accepted in browser fields, and server-returned finding, contradiction, and draft strings are rendered through `textContent` rather than HTML injection. The Docker/Compose deployment runs that same API/UI process as non-root and uses loopback-only publishing by default, a read-only root filesystem, ephemeral `/tmp`, dropped capabilities, and `no-new-privileges`. It adds no persistence or proxy layer. The provider-neutral AI contract itself performs no network call and loads no credentials. The optional `OllamaProvider` and `OpenAICompatibleProvider` are explicit outbound-network surfaces. Each sends only supplied system/user prompts when `generate()` is called, performs no request during construction, does not persist or log prompts/responses, disables streaming, and caps response reads. Ollama defaults to loopback. The OpenAI-compatible adapter requires an explicit API root and may send an optional caller-supplied Bearer key; the runtime resolver reads that key only from server environment and neither adapter nor API logs/returns it. Advisory contradiction analysis sends the supplied specification to the explicitly configured provider, treats specification content as untrusted prompt data, accepts only a bounded JSON result, and rejects contradiction evidence unless both quoted statements are verbatim source substrings. It does not persist prompts or model output and cannot alter deterministic rule controls. Improved-spec drafting has the same explicit provider egress boundary, JSON-wraps the source and optional contradiction context as untrusted data, validates only bounded Markdown shape, and must still be treated as untrusted advisory model output requiring human review.
