# Project configuration

SpecForge Gate can read local project settings from `.specgate.yml`.

## Runtime dependency

Configuration parsing uses [PyYAML](https://pyyaml.org/) as a runtime dependency. PyYAML is a maintained YAML parser distributed under the MIT license, which is compatible with SpecForge Gate's MIT license.

The deterministic rule engine remains free of network and provider dependencies: configuration is read only from local files, and SpecForge Gate does not download remote configuration.

## Discovery

`specgate check path/to/task.md` discovers the first `.specgate.yml` found by walking from the current working directory toward the filesystem root. If no configuration file exists, SpecForge Gate keeps the built-in default behavior.

Use `--config path/to/file.yml` to supply an explicit configuration file instead of discovery.

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
- `exclude`: optional list of path patterns. Matching files are skipped and return a passing empty report.

Unknown top-level fields, unknown rule IDs, unsupported versions, invalid severities, invalid booleans, and invalid YAML return exit code `2` with an error naming the invalid field where possible.

## Examples

- Start from [`.specgate.example.yml`](../.specgate.example.yml) for a balanced configuration.
- Use [`examples/config/strict.specgate.yml`](../examples/config/strict.specgate.yml) when warnings should block delivery.
- Use [`examples/config/relaxed.specgate.yml`](../examples/config/relaxed.specgate.yml) when teams intentionally suppress optional rules.
