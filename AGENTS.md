# AGENTS.md

- Keep the deterministic core free of network and provider dependencies.
- Every rule requires positive and negative tests.
- Stable rule IDs are public API; do not reuse or silently change their meaning.
- `main` must remain releasable.
- New behavior starts with an Issue containing scope, out-of-scope, and acceptance criteria.
- Use GitHub-hosted runners for untrusted public pull requests.
