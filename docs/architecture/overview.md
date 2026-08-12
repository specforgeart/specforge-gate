# Architecture overview

```text
Input → Document parser → Rule engine → Report model → CLI / GitHub Action / REST API / Web UI
```

The core has no network dependency. The CLI, GitHub Action, REST API, and same-origin web UI preserve the same deterministic `analyze_text()` boundary. The optional `specforge_gate.ai` layer contains the provider-neutral contract, Ollama and OpenAI-compatible adapters, advisory contradiction analysis, and conservative improved-spec drafting. The REST API and web UI now expose AI only through an explicit separate review path; provider network I/O occurs only after that path is invoked. Rules return structured findings with stable IDs, severity, location, explanation, and suggested correction; advisory AI results do not modify those findings.

See [`../architecture.md`](../architecture.md) for the public architecture entry point with the GitHub-compatible Mermaid diagram and interface boundaries.
