from pathlib import Path

import pytest

from specforge_gate.cli import main
from specforge_gate.config import ConfigError, ProjectConfig, load_project_config
from specforge_gate.engine import analyze_text
from specforge_gate.models import Severity
from specforge_gate.reporters import render_json, render_markdown, render_text


def test_disabled_rule_suppresses_finding() -> None:
    report = analyze_text(
        "# Task\n\nDo it fast.\n",
        config=ProjectConfig(rules={"SG101": _rule(enabled=False)}),
    )
    assert {finding.rule_id for finding in report.findings}.isdisjoint({"SG101"})


def test_enabled_rule_still_reports_finding() -> None:
    report = analyze_text(
        "# Task\n\nDo it fast.\n",
        config=ProjectConfig(rules={"SG101": _rule(enabled=True)}),
    )
    assert any(finding.rule_id == "SG101" for finding in report.findings)


def test_severity_override_reaches_all_reporters() -> None:
    report = analyze_text(
        "# Task\n\nDo it fast.\n",
        config=ProjectConfig(rules={"SG101": _rule(severity=Severity.ERROR)}),
    )
    finding = next(item for item in report.findings if item.rule_id == "SG101")
    assert finding.severity is Severity.ERROR
    assert "[ERROR] SG101" in render_text(report)
    assert '"severity": "error"' in render_json(report)
    assert "`SG101` · error" in render_markdown(report)


def test_default_severity_remains_warning_without_override() -> None:
    report = analyze_text("# Task\n\nDo it fast.")
    finding = next(item for item in report.findings if item.rule_id == "SG101")
    assert finding.severity is Severity.WARNING


def test_cli_discovers_config_from_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".specgate.yml").write_text(
        "version: 1\nrules:\n  SG001:\n    enabled: false\n", encoding="utf-8"
    )
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["check", str(task), "--fail-on", "none"]) == 0


def test_cli_explicit_config_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = tmp_path / "custom.yml"
    config.write_text("version: 1\nrules:\n  SG101:\n    severity: error\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")
    assert main(["check", str(task), "--config", str(config), "--fail-on", "none"]) == 0
    assert "[ERROR] SG101" in capsys.readouterr().out


def test_invalid_config_returns_exit_code_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nlanguage: de\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(task)]) == 2
    assert "config.language" in capsys.readouterr().err


def test_valid_language_is_accepted(tmp_path: Path) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nlanguage: ru\n", encoding="utf-8")
    assert load_project_config(config).language == "ru"


def test_excluded_path_is_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".specgate.yml").write_text(
        'version: 1\nexclude:\n  - "docs/archive/**"\n', encoding="utf-8"
    )
    archive = tmp_path / "docs" / "archive"
    archive.mkdir(parents=True)
    task = archive / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["check", str(task)]) == 0


def test_non_excluded_path_is_analyzed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".specgate.yml").write_text(
        'version: 1\nexclude:\n  - "docs/archive/**"\n', encoding="utf-8"
    )
    task = tmp_path / "docs" / "task.md"
    task.parent.mkdir()
    task.write_text("# Task\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["check", str(task)]) == 1


def test_invalid_severity_names_field(tmp_path: Path) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nrules:\n  SG001:\n    severity: fatal\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="config.rules.SG001.severity"):
        load_project_config(config)


def test_valid_rule_configuration_loads(tmp_path: Path) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nrules:\n  SG001:\n    severity: warning\n", encoding="utf-8")
    assert load_project_config(config).severity_for("SG001", Severity.ERROR) is Severity.WARNING


def _rule(*, enabled: bool = True, severity: Severity | None = None):
    from specforge_gate.config import RuleConfig

    return RuleConfig(enabled=enabled, severity=severity)


def test_invalid_yaml_returns_exit_code_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nrules:\n  SG001: [\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(task)]) == 2
    assert "invalid YAML" in capsys.readouterr().err


def test_unknown_top_level_field_returns_exit_code_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nprofiles: {}\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(task)]) == 2
    assert "config.profiles" in capsys.readouterr().err


def test_unknown_rule_id_returns_exit_code_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text("version: 1\nrules:\n  missing-goal:\n    enabled: false\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(task)]) == 2
    assert "config.rules.missing-goal" in capsys.readouterr().err


def test_explicit_config_excludes_supplied_file(tmp_path: Path) -> None:
    config = tmp_path / "custom.yml"
    config.write_text('version: 1\nexclude:\n  - "task.md"\n', encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(task), "--config", str(config)]) == 0


def test_backward_compatibility_without_configuration(tmp_path: Path) -> None:
    task = tmp_path / "task.md"
    task.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")
    configured = main(["check", str(task), "--fail-on", "none"])
    assert configured == 0
