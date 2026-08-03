"""Console, JSON, and Markdown reporters."""

from __future__ import annotations

import json

from specforge_gate.models import AnalysisReport, Severity


def render_text(report: AnalysisReport) -> str:
    lines = [
        report.status.value,
        "",
        f"Errors: {report.count(Severity.ERROR)}",
        f"Warnings: {report.count(Severity.WARNING)}",
        f"Info: {report.count(Severity.INFO)}",
    ]
    if report.findings:
        lines.extend(["", "Findings"])
        for finding in report.findings:
            location = f" line {finding.line}" if finding.line else ""
            lines.append(f"- [{finding.severity.value.upper()}] {finding.rule_id}{location}: {finding.message}")
            lines.append(f"  Fix: {finding.suggestion}")
    return "\n".join(lines)


def render_json(report: AnalysisReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def render_markdown(report: AnalysisReport) -> str:
    lines = [
        f"# SpecForge Gate: {report.status.value}",
        "",
        "| Severity | Count |",
        "|---|---:|",
        f"| Error | {report.count(Severity.ERROR)} |",
        f"| Warning | {report.count(Severity.WARNING)} |",
        f"| Info | {report.count(Severity.INFO)} |",
    ]
    if report.findings:
        lines.extend(["", "## Findings", ""])
        for finding in report.findings:
            location = f" (line {finding.line})" if finding.line else ""
            lines.extend(
                [
                    f"### `{finding.rule_id}` · {finding.severity.value}{location}",
                    "",
                    finding.message,
                    "",
                    f"**Suggested fix:** {finding.suggestion}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
