# Architecture overview

```text
Input → Document parser → Rule engine → Report model → CLI / GitHub Action / planned API
```

The core has no network dependency. The CLI and GitHub Action call the same `analyze_text()` function; planned interfaces must preserve that boundary. Rules return structured findings with stable IDs, severity, location, explanation, and suggested correction.

See [`../architecture.md`](../architecture.md) for the public architecture entry point with the GitHub-compatible Mermaid diagram and interface boundaries.
