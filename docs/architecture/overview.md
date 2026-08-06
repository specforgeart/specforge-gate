# Architecture overview

```text
Input → Document parser → Rule engine → Report model → CLI / planned API / planned GitHub Action
```

The core has no network dependency. The current CLI and planned external interfaces call the same `analyze_text()` function. Rules return structured findings with stable IDs, severity, location, explanation, and suggested correction.

See [`../architecture.md`](../architecture.md) for the public architecture entry point with the GitHub-compatible Mermaid diagram and planned-interface boundaries.
