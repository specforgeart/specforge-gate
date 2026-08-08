# Architecture

SpecForge Gate is deterministic-first. The implemented core reads local input, parses it, runs deterministic rules, and emits structured reports through the current CLI outputs. The available GitHub Action, REST API, web UI, and container deployment preserve the same core boundary without adding network or provider dependencies to it.

```mermaid
flowchart TD
    subgraph Core["Deterministic core — available"]
        A["Input files and directories"] --> B["Markdown/text parser"]
        B --> C["Deterministic rule engine"]
        C --> D["Findings and report model"]
    end

    D --> E["CLI — available"]
    E --> F["Text output — available"]
    E --> G["JSON output — available"]
    E --> H["Markdown output — available"]

    D --> I["GitHub Action — available"]
    I --> O["PR file selection — local git diff"]
    I --> P["GitHub job summary"]
    D --> J["REST API — available"]
    D --> K["Web UI — available"]
    J --> Q["Docker / Compose — available"]

    subgraph AI["Optional AI layer — planned and separate"]
        L["Provider interface — available"]
        R["Ollama adapter — available"]
        M["Contradiction analysis — planned"]
        N["Improved-spec draft — planned"]
    end

    D -. future optional input .-> L
    L --> R
    L -. planned .-> M
    L -. planned .-> N
```

## Available flow

1. The CLI receives one or more local files or directories.
2. Directory inputs expand to Markdown, Markdown-like, and text files.
3. The parser extracts sections and lines for deterministic analysis.
4. Rules emit findings with stable IDs, severity, location, explanation, and suggested correction.
5. The report model renders text, JSON, or Markdown output.
6. Exit codes are controlled by `--fail-on` and remain compatibility-sensitive.

## GitHub Action interface

The reusable composite action is an available interface layer. It provisions Python, installs the package from the action checkout, selects pull-request Markdown changes with a local three-dot `git diff`, applies project configuration, runs the deterministic engine, and writes a Markdown job summary. It requires no API-write token and does not send specification content outside the runner.

## REST API interface

The optional REST API is an available stateless interface layer. It accepts inline text at `POST /v1/check`, maps validated inline rule configuration into the existing `ProjectConfig`, calls the same `analyze_text()` core, and returns the existing structured report contract. It never accepts request-selected filesystem paths or URLs. FastAPI/Uvicorn remain optional interface dependencies and are not dependencies of the deterministic core.

## Web UI interface

The minimal web UI is an available same-origin interface served by the optional FastAPI process at `/`. It is a self-contained HTML/CSS/JavaScript page with no frontend build toolchain or external runtime assets. The browser sends pasted text only to the existing `/v1/check` endpoint, renders returned fields through DOM text nodes, supports severity filtering, and can copy the current deterministic report as Markdown. It adds no dependency or behavior to the deterministic core.

## Container interface

The Docker image and one-service Compose deployment package the existing FastAPI process rather than creating a new product service. The container serves the same REST API and web UI, runs as a non-root user, and relies on the existing `/healthz` endpoint. Compose binds to loopback by default and adds a read-only root filesystem, ephemeral `/tmp`, dropped capabilities, and `no-new-privileges`. The container layer adds no persistence, database, reverse proxy, authentication, or provider dependency.

## Optional AI boundary

The provider-neutral AI contract and `OllamaProvider` are available under `specforge_gate.ai`. The contract remains separate from the deterministic core. `OllamaProvider` performs explicit outbound HTTP only when invoked and defaults to loopback; no deterministic check imports or calls it. The OpenAI-compatible adapter and AI-powered analysis remain planned. Optional AI code must not change stable rule IDs, current deterministic output contracts, or exit-code semantics. See [`ai-provider-interface.md`](ai-provider-interface.md) and [`ollama.md`](ollama.md).

## Related details

The older [architecture overview](architecture/overview.md) remains a concise internal summary and should align with this public entry point.
