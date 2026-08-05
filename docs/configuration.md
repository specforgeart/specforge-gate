# Project configuration

SpecForge Gate can read local project settings from `.specgate.yml`.

## Runtime dependency

Configuration parsing uses [PyYAML](https://pyyaml.org/) as a runtime dependency. PyYAML is a maintained YAML parser distributed under the MIT license, which is compatible with SpecForge Gate's MIT license.

The deterministic rule engine remains free of network and provider dependencies: configuration is read only from local files, and SpecForge Gate does not download remote configuration.

## Discovery

`specgate check path/to/task.md` discovers the first `.specgate.yml` found by walking from the current working directory toward the filesystem root. If no configuration file exists, SpecForge Gate keeps the built-in default behavior.

Use `--config path/to/file.yml` to supply an explicit configuration file instead of discovery.

## Checking more than one input

`specgate check` accepts one or more files or directories. Directories are scanned recursively for `.md`, `.markdown`, and `.txt` files in deterministic path order.

A single explicit file keeps the original output shape for text, JSON, and Markdown. Multiple explicit files or any directory input produce a deterministic aggregate report. Text and Markdown group results by source path. JSON returns a top-level `summary` and a `reports` array containing the existing per-file report schema.

Exit code behavior is aggregated across analyzed files: invalid configuration or unreadable input returns `2`; otherwise `--fail-on error` returns `1` if any analyzed file has an error, `--fail-on warning` returns `1` if any analyzed file has an error or warning, and `--fail-on none` always returns `0`.

## Shape

```yaml
version: 1
language: ru
rules:
  SG001:
    enabled: true
    severity: error
  SG101:
    enabled: false
exclude:
  - docs/archive/**
  - "**/generated/**"
```

## Fields

- `version`: required configuration format version. The only supported value is `1`.
- `language`: optional language hint. Supported values are `auto`, `ru`, and `en`.
- `rules`: optional mapping keyed by stable rule ID (`SG001`, `SG002`, etc.).
  - `enabled`: optional boolean. Set to `false` to suppress that rule.
  - `severity`: optional override. Supported values are `error`, `warning`, and `info`.
- `exclude`: optional list of path patterns applied only to files discovered while checking directories. A file explicitly passed to `specgate check path/to/task.md` is still analyzed even when it matches an exclude pattern.

Unknown top-level fields, unknown rule IDs, unsupported versions, invalid severities, invalid booleans, and invalid YAML return exit code `2` with an error naming the invalid field where possible.

## Examples

- Start from [`.specgate.example.yml`](../.specgate.example.yml) for a balanced configuration.
- Use [`examples/config/strict.specgate.yml`](../examples/config/strict.specgate.yml) when warnings should block delivery.
- Use [`examples/config/relaxed.specgate.yml`](../examples/config/relaxed.specgate.yml) when teams intentionally suppress optional rules.
