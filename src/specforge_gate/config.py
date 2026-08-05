"""Project configuration loading and validation."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from yaml import YAMLError, safe_load

from specforge_gate.models import Severity
from specforge_gate.rules import builtin_rules

CONFIG_FILENAME = ".specgate.yml"
SUPPORTED_VERSION = 1
LANGUAGES = frozenset({"auto", "ru", "en"})


class ConfigError(ValueError):
    """Raised when project configuration cannot be loaded or validated."""


@dataclass(frozen=True, slots=True)
class RuleConfig:
    enabled: bool = True
    severity: Severity | None = None


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    version: int = SUPPORTED_VERSION
    language: str = "auto"
    rules: dict[str, RuleConfig] = field(default_factory=dict)
    exclude: tuple[str, ...] = ()
    path: Path | None = None

    def is_rule_enabled(self, rule_id: str) -> bool:
        return self.rules.get(rule_id, RuleConfig()).enabled

    def severity_for(self, rule_id: str, default: Severity) -> Severity:
        return self.rules.get(rule_id, RuleConfig()).severity or default

    def excludes(self, path: Path) -> bool:
        candidates = [path.as_posix()]
        if self.path is not None:
            with suppress(ValueError):
                relative_path = path.resolve().relative_to(self.path.parent.resolve())
                candidates.append(relative_path.as_posix())
        return any(
            fnmatch(candidate, pattern)
            for candidate in candidates
            for pattern in self.exclude
        )


def discover_config(start: Path) -> Path | None:
    directory = start if start.is_dir() else start.parent
    for candidate_dir in (directory, *directory.parents):
        candidate = candidate_dir / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_project_config(path: Path | None = None, *, start: Path | None = None) -> ProjectConfig:
    config_path = path or discover_config(start or Path.cwd())
    if config_path is None:
        return ProjectConfig()
    try:
        data = safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"config: cannot read {config_path}: {exc}") from exc
    except UnicodeError as exc:
        raise ConfigError(f"config: cannot decode {config_path}: {exc}") from exc
    except YAMLError as exc:
        raise ConfigError(f"config: invalid YAML in {config_path}: {exc}") from exc
    return _validate_config(data, config_path)


def _validate_config(data: object, path: Path) -> ProjectConfig:
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError("config: root must be a mapping")

    allowed = {"version", "language", "rules", "exclude"}
    for key in data:
        if key not in allowed:
            raise ConfigError(f"config.{key}: unknown field")

    version = data.get("version")
    if version != SUPPORTED_VERSION:
        raise ConfigError(f"config.version: expected {SUPPORTED_VERSION}")

    language = data.get("language", "auto")
    if not isinstance(language, str) or language not in LANGUAGES:
        raise ConfigError("config.language: expected one of auto, ru, en")

    raw_rules = data.get("rules", {})
    if not isinstance(raw_rules, dict):
        raise ConfigError("config.rules: expected mapping")

    known_rule_ids = {rule.rule_id for rule in builtin_rules()}
    rules: dict[str, RuleConfig] = {}
    for rule_id, raw_rule in raw_rules.items():
        if not isinstance(rule_id, str):
            raise ConfigError("config.rules: rule id must be a string")
        if rule_id not in known_rule_ids:
            raise ConfigError(f"config.rules.{rule_id}: unknown rule ID")
        if raw_rule is None:
            raw_rule = {}
        if not isinstance(raw_rule, dict):
            raise ConfigError(f"config.rules.{rule_id}: expected mapping")
        rule_allowed = {"enabled", "severity"}
        for key in raw_rule:
            if key not in rule_allowed:
                raise ConfigError(f"config.rules.{rule_id}.{key}: unknown field")
        enabled = raw_rule.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ConfigError(f"config.rules.{rule_id}.enabled: expected boolean")
        severity = raw_rule.get("severity")
        parsed_severity = None
        if severity is not None:
            try:
                parsed_severity = Severity(severity)
            except ValueError as exc:
                raise ConfigError(
                    f"config.rules.{rule_id}.severity: expected error, warning, or info"
                ) from exc
        rules[rule_id] = RuleConfig(enabled=enabled, severity=parsed_severity)

    raw_exclude = data.get("exclude", [])
    if not isinstance(raw_exclude, list) or not all(isinstance(item, str) for item in raw_exclude):
        raise ConfigError("config.exclude: expected list of strings")

    return ProjectConfig(
        version=version,
        language=language,
        rules=rules,
        exclude=tuple(raw_exclude),
        path=path,
    )
