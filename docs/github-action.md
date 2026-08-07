# GitHub Action

SpecForge Gate includes a reusable composite action for deterministic checks in pull requests. It reads repository files on the runner, sends no specification content to external services, posts no pull-request comments, and requires only `contents: read` permission.

## Pull-request workflow

```yaml
name: SpecForge Gate

on:
  pull_request:
    paths:
      - "**/*.md"
      - "**/*.markdown"
      - ".specgate.yml"

permissions:
  contents: read

jobs:
  requirements:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: specforgeart/specforge-gate@main
        with:
          fail-on: error
```

The pre-release example uses `@main` so the action is immediately usable after merge. For a stable consumer workflow, pin a reviewed commit SHA or a release tag that contains the action.

`fetch-depth: 0` is required in automatic pull-request mode. The action calculates a local three-dot diff between the pull request base and head commits; it does not call the GitHub API to enumerate files.

Automatic pull-request mode selects only existing files with these statuses and suffixes:

- added `.md` and `.markdown` files;
- modified `.md` and `.markdown` files;
- renamed files whose new path ends in `.md` or `.markdown`.

Deleted files and non-Markdown files are ignored.

## Explicit paths

Use `paths` for workflow dispatch, smoke tests, or a fixed repository subset. Provide one file, directory, or glob per line:

```yaml
- uses: specforgeart/specforge-gate@main
  with:
    paths: |
      requirements/
      docs/specifications/**/*.md
    fail-on: warning
```

Explicit files may use `.md`, `.markdown`, or `.txt`. Directories recursively discover those suffixes. A glob with no matches produces a successful PASS summary with zero checked files. A missing literal path is an actionable configuration error.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `paths` | empty | Newline-delimited explicit paths. Empty means automatic PR selection. |
| `fail-on` | `error` | `none`, `warning`, or `error`, with the same threshold semantics as the CLI. |
| `config` | empty | Explicit `.specgate.yml` path relative to the checked repository. Empty uses normal discovery. |
| `python-version` | `3.11` | Python runtime provisioned through `actions/setup-python`. |

Configuration exclusions, disabled rules, severity overrides, and inline suppressions apply to Action analysis. Unlike direct CLI file arguments, Action-selected files are filtered through configured `exclude` patterns before analysis.

## Outputs

| Output | Meaning |
|---|---|
| `status` | `PASS`, `NEEDS WORK`, or `ERROR`. |
| `files` | Number of checked files. |
| `errors` | Error finding count. |
| `warnings` | Warning finding count. |
| `info` | Informational finding count. |
| `total` | Total finding count. |

Every run writes a GitHub-flavored Markdown job summary containing status, counts, checked files, and findings. Oversized summaries are truncated below GitHub's per-step limit while scalar outputs retain complete counts. Invalid configuration, unreadable files, malformed suppressions, and unavailable PR commits return exit code `2` without a Python traceback.

## Security boundary

- The consumer workflow needs only `contents: read`.
- The action does not consume `GITHUB_TOKEN` and performs no API writes.
- It does not create PR comments, issue comments, or SARIF uploads.
- Specifications remain on the GitHub-hosted runner.
- The deterministic parser and rule engine remain free of network and provider dependencies.

The initial action smoke workflow targets `ubuntu-latest`. Other runner operating systems are not part of the current verified contract.
