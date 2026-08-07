from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from specforge_gate.config import ConfigError, ProjectConfig, RuleConfig, load_project_config
from specforge_gate.document import Document
from specforge_gate.engine import analyze_text
from specforge_gate.models import AnalysisReport, Finding, Severity
from specforge_gate.reporters import render_json, render_markdown, render_text
from specforge_gate.rules.structure import structural_rules
from specforge_gate.suppression import SuppressionError, parse_suppressions


@dataclass(frozen=True)
class StaticRule:
    rule_id: str
    findings: tuple[Finding, ...]

    def check(self, document: Document) -> list[Finding]:
        del document
        return list(self.findings)


def _sample_report() -> AnalysisReport:
    return AnalysisReport(
        source="задача.md",
        findings=[
            Finding(
                rule_id="SG001",
                severity=Severity.ERROR,
                message="Goal missing.",
                suggestion="Add goal.",
            ),
            Finding(
                rule_id="SG101",
                severity=Severity.WARNING,
                message="Vague wording.",
                suggestion="Be precise.",
                line=7,
                excerpt="fast",
            ),
            Finding(
                rule_id="SG103",
                severity=Severity.INFO,
                message="Compound requirement.",
                suggestion="Split it.",
                line=9,
                excerpt="create and export",
            ),
        ],
    )


def test_text_reporter_exact_contract() -> None:
    report = _sample_report()
    assert render_text(report) == (
        "NEEDS WORK\n"
        "\n"
        "Errors: 1\n"
        "Warnings: 1\n"
        "Info: 1\n"
        "\n"
        "Findings\n"
        "- [ERROR] SG001: Goal missing.\n"
        "  Fix: Add goal.\n"
        "- [WARNING] SG101 line 7: Vague wording.\n"
        "  Fix: Be precise.\n"
        "- [INFO] SG103 line 9: Compound requirement.\n"
        "  Fix: Split it."
    )


def test_json_reporter_exact_contract() -> None:
    report = _sample_report()
    assert render_json(report) == json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    assert "задача.md" in render_json(report)
    assert "\\u0437" not in render_json(report)


def test_markdown_reporter_exact_contract() -> None:
    report = _sample_report()
    assert render_markdown(report) == (
        "# SpecForge Gate: NEEDS WORK\n"
        "\n"
        "| Severity | Count |\n"
        "|---|---:|\n"
        "| Error | 1 |\n"
        "| Warning | 1 |\n"
        "| Info | 1 |\n"
        "\n"
        "## Findings\n"
        "\n"
        "### `SG001` · error\n"
        "\n"
        "Goal missing.\n"
        "\n"
        "**Suggested fix:** Add goal.\n"
        "\n"
        "### `SG101` · warning (line 7)\n"
        "\n"
        "Vague wording.\n"
        "\n"
        "**Suggested fix:** Be precise.\n"
        "\n"
        "### `SG103` · info (line 9)\n"
        "\n"
        "Compound requirement.\n"
        "\n"
        "**Suggested fix:** Split it.\n"
    )


def test_empty_reporter_contracts() -> None:
    report = AnalysisReport(source="empty.md")
    assert render_text(report) == "PASS\n\nErrors: 0\nWarnings: 0\nInfo: 0"
    assert render_markdown(report) == (
        "# SpecForge Gate: PASS\n"
        "\n"
        "| Severity | Count |\n"
        "|---|---:|\n"
        "| Error | 0 |\n"
        "| Warning | 0 |\n"
        "| Info | 0 |\n"
    )


def test_engine_applies_suppression_override_copy_and_sorting() -> None:
    rules = (
        StaticRule(
            "ZZ002",
            (
                Finding("ZZ002", Severity.WARNING, "late", "fix late"),
                Finding("ZZ002", Severity.ERROR, "early", "fix early", line=1, excerpt="x"),
            ),
        ),
        StaticRule(
            "ZZ001",
            (Finding("ZZ001", Severity.ERROR, "suppressed", "fix", line=2),),
        ),
    )
    report = analyze_text(
        "<!-- specgate-ignore-next-line ZZ001 -->\ncontent\n",
        source="custom.md",
        rules=rules,
        config=ProjectConfig(rules={"ZZ002": RuleConfig(severity=Severity.INFO)}),
    )

    assert report.source == "custom.md"
    assert report.findings == [
        Finding("ZZ002", Severity.INFO, "early", "fix early", line=1, excerpt="x"),
        Finding("ZZ002", Severity.INFO, "late", "fix late"),
    ]


def test_structural_rule_registry_exact_contract() -> None:
    snapshot = [
        (rule.rule_id, rule.aliases, rule.title, rule.severity, rule.suggestion)
        for rule in structural_rules()
    ]
    assert snapshot == [
        (
            "SG001",
            ("goal", "objective", "цель", "задача"),
            "Goal",
            Severity.ERROR,
            "State the user or business outcome in one or two sentences.",
        ),
        (
            "SG002",
            ("expected result", "deliverable", "результат", "что должно получиться"),
            "Expected result",
            Severity.ERROR,
            "Describe the concrete artifact, behavior, or state that must exist after delivery.",
        ),
        (
            "SG003",
            (
                "acceptance criteria",
                "definition of done",
                "критерии приёмки",
                "критерии приемки",
                "условия приёмки",
            ),
            "Acceptance criteria",
            Severity.ERROR,
            "Add observable pass/fail criteria as a checklist or numbered list.",
        ),
        (
            "SG004",
            ("out of scope", "non-goals", "не входит", "вне scope", "вне скоупа"),
            "Out of scope",
            Severity.WARNING,
            "Explicitly list excluded capabilities to prevent scope expansion.",
        ),
        (
            "SG005",
            (
                "error handling",
                "edge cases",
                "negative scenarios",
                "ошибки",
                "граничные случаи",
                "негативные сценарии",
            ),
            "Errors and edge cases",
            Severity.WARNING,
            (
                "Describe invalid input, unavailable dependencies, "
                "permission failures, and boundaries."
            ),
        ),
    ]


def test_structural_rule_missing_and_present_contract() -> None:
    rule = structural_rules()[0]
    missing = rule.check(Document.parse("# Task\n"))
    assert missing == [
        Finding(
            rule_id="SG001",
            severity=Severity.ERROR,
            message="Missing or empty section: Goal.",
            suggestion="State the user or business outcome in one or two sentences.",
        )
    ]
    assert rule.check(Document.parse("## Goal\nA measurable outcome.\n")) == []
    assert rule.check(Document.parse("## Goal\n   \n")) == missing


def test_suppression_parser_exact_mapping_and_sanitized_text() -> None:
    text = "\r\n".join(
        [
            "<!-- specgate-ignore-file sg004, SG005 -->",
            "<!-- specgate-ignore-next-line SG101 -->",
            "",
            "content",
            "<!-- specgate-ignore-next-line SG102 -->",
            "<!-- ordinary comment -->",
            "next",
        ]
    )
    sanitized, suppressions = parse_suppressions(
        text,
        known_rule_ids={"SG004", "SG005", "SG101", "SG102"},
    )

    assert sanitized == "\n\n\ncontent\n\n<!-- ordinary comment -->\nnext"
    assert suppressions.file_rule_ids == frozenset({"SG004", "SG005"})
    assert dict(suppressions.next_line_rule_ids) == {
        4: frozenset({"SG101"}),
        6: frozenset({"SG102"}),
    }
    assert suppressions.suppresses("sg004", None)
    assert suppressions.suppresses("SG101", 4)
    assert suppressions.suppresses("SG102", 6)
    assert not suppressions.suppresses("SG101", 5)
    assert not suppressions.suppresses("SG102", 7)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("- item\n", "config: root must be a mapping"),
        ("language: en\n", "config.version: expected 1"),
        ("version: 1\nextra: true\n", "config.extra: unknown field"),
        ("version: 1\nlanguage: 2\n", "config.language: expected one of auto, ru, en"),
        ("version: 1\nrules: []\n", "config.rules: expected mapping"),
        (
            "version: 1\nrules:\n  1:\n    enabled: true\n",
            "config.rules: rule id must be a string",
        ),
        (
            "version: 1\nrules:\n  SG999:\n    enabled: true\n",
            "config.rules.SG999: unknown rule ID",
        ),
        (
            "version: 1\nrules:\n  SG001: true\n",
            "config.rules.SG001: expected mapping",
        ),
        (
            "version: 1\nrules:\n  SG001:\n    extra: true\n",
            "config.rules.SG001.extra: unknown field",
        ),
        (
            "version: 1\nrules:\n  SG001:\n    enabled: \"yes\"\n",
            "config.rules.SG001.enabled: expected boolean",
        ),
        (
            "version: 1\nrules:\n  SG001:\n    severity: fatal\n",
            "config.rules.SG001.severity: expected error, warning, or info",
        ),
        ("version: 1\nexclude: task.md\n", "config.exclude: expected list of strings"),
        ("version: 1\nexclude:\n  - 7\n", "config.exclude: expected list of strings"),
    ],
)
def test_config_validation_exact_errors(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / ".specgate.yml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError) as error:
        load_project_config(path)
    assert str(error.value) == message


def test_config_full_valid_mapping_exact_contract(tmp_path: Path) -> None:
    path = tmp_path / ".specgate.yml"
    path.write_text(
        "version: 1\n"
        "language: en\n"
        "rules:\n"
        "  SG001:\n"
        "    enabled: false\n"
        "    severity: warning\n"
        "  SG002:\n"
        "exclude:\n"
        "  - docs/archive/**\n",
        encoding="utf-8",
    )
    assert load_project_config(path) == ProjectConfig(
        version=1,
        language="en",
        rules={
            "SG001": RuleConfig(enabled=False, severity=Severity.WARNING),
            "SG002": RuleConfig(),
        },
        exclude=("docs/archive/**",),
        path=path,
    )


@pytest.mark.parametrize(
    ("text", "known", "message", "line"),
    [
        (
            "<!-- specgate-ignore-file -->\n",
            {"SG001"},
            "suppression directive requires at least one rule ID",
            1,
        ),
        (
            "<!-- specgate-ignore-file SG-001 -->\n",
            {"SG001"},
            "malformed suppression rule ID list",
            1,
        ),
        (
            "<!-- specgate-ignore-file SG999 -->\n",
            {"SG001"},
            "unknown suppression rule ID: SG999",
            1,
        ),
        (
            "content\n<!-- specgate-ignore-file SG001 -->\n",
            {"SG001"},
            "ignore-file must appear in the document preamble",
            2,
        ),
        (
            "<!-- specgate-ignore-next-line SG001 -->\n",
            {"SG001"},
            "ignore-next-line must target a following content line",
            1,
        ),
    ],
)
def test_suppression_exact_errors(
    text: str,
    known: set[str],
    message: str,
    line: int,
) -> None:
    with pytest.raises(SuppressionError) as error:
        parse_suppressions(text, known_rule_ids=known)
    assert str(error.value) == message
    assert error.value.line == line
