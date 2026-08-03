"""Analysis engine."""

from __future__ import annotations

from collections.abc import Iterable

from specforge_gate.document import Document
from specforge_gate.models import AnalysisReport, Finding
from specforge_gate.rules import Rule, builtin_rules


def analyze_text(
    text: str,
    *,
    source: str = "<text>",
    rules: Iterable[Rule] | None = None,
) -> AnalysisReport:
    document = Document.parse(text)
    findings: list[Finding] = []
    for rule in rules or builtin_rules():
        findings.extend(rule.check(document))
    findings.sort(key=lambda item: (item.line is None, item.line or 0, item.rule_id))
    return AnalysisReport(source=source, findings=findings)
