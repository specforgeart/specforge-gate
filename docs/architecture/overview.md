# Architecture overview

```text
Input → Document parser → Rule engine → Report model → CLI / GitHub Action / REST API / Web UI
```

The core has no network dependency. The CLI, GitHub Action, REST API, and same-origin web UI all preserve the same `analyze_text()` boundary; planned interfaces must preserve it too. Rules return structured findings with stable IDs, severity, location, explanation, and suggested correction.

See [`../architecture.md`](../architecture.md) for the public architecture entry point with the GitHub-compatible Mermaid diagram and interface boundaries.
