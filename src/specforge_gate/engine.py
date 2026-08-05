"""Analysis engine."""

from __future__ import annotations

from collections.abc import Iterable

from specforge_gate.config import ProjectConfig
from specforge_gate.document import Document
from specforge_gate.models import AnalysisReport, Finding
from specforge_gate.rules import Rule, builtin_rules


def analyze_text(
    text: str,
    *,
    source: str = "<text>",
    rules: Iterable[Rule] | None = None,
    config: ProjectConfig | None = None,
) -> AnalysisReport:
    document = Document.parse(text)
    findings: list[Finding] = []
    project_config = config or ProjectConfig()
    for rule in rules or builtin_rules():
        if project_config.is_rule_enabled(rule.rule_id):
            for finding in rule.check(document):
                findings.append(
                    Finding(
                        rule_id=finding.rule_id,
                        severity=project_config.severity_for(finding.rule_id, finding.severity),
                        message=finding.message,
                        suggestion=finding.suggestion,
                        line=finding.line,
                        excerpt=finding.excerpt,
                    )
                )
    findings.sort(key=lambda item: (item.line is None, item.line or 0, item.rule_id))
    return AnalysisReport(source=source, findings=findings)
