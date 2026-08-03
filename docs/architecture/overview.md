# Architecture

```text
Input → Document parser → Rule engine → Report model → CLI / API / GitHub Action
```

The core has no network dependency. Interfaces call the same `analyze_text()` function. Rules return structured findings with stable IDs, severity, location, explanation, and suggested correction.
