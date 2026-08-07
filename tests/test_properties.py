from __future__ import annotations

import json
from collections import Counter

from hypothesis import given, settings
from hypothesis import strategies as st

from specforge_gate.config import ProjectConfig, RuleConfig
from specforge_gate.document import Document
from specforge_gate.engine import analyze_text
from specforge_gate.models import Severity
from specforge_gate.reporters import render_json, render_markdown
from specforge_gate.rules import builtin_rules

KNOWN_RULE_IDS = tuple(rule.rule_id for rule in builtin_rules())
KNOWN_RULE_ID_SET = frozenset(KNOWN_RULE_IDS)
SEVERITIES = tuple(Severity)

SAFE_LINE = st.text(
    alphabet=st.characters(exclude_categories=("Cs",), exclude_characters="\r\n"),
    max_size=80,
).filter(lambda value: "specgate-" not in value.casefold())
TEXT_CASES = st.lists(SAFE_LINE, min_size=0, max_size=8)
NEWLINES = st.sampled_from(("\n", "\r\n", "\r"))

VALID_SPEC = """# Task

## Goal
Ship a deterministic result.

## Expected result
A Markdown report.

## Out of scope
No network calls.

## Acceptance criteria
- Given 3 findings, when analysis runs, then the report contains 3 findings.

## Errors and edge cases
- Invalid input is reported.
"""

TRIGGERS = {
    "SG001": """# Task
## Expected result
A result.
## Acceptance criteria
- Given input, when run, then output exists.
## Out of scope
None.
## Errors and edge cases
- Invalid input.
""",
    "SG002": """# Task
## Goal
Ship it.
## Acceptance criteria
- Given input, when run, then output exists.
## Out of scope
None.
## Errors and edge cases
- Invalid input.
""",
    "SG003": """# Task
## Goal
Ship it.
## Expected result
A result.
## Out of scope
None.
## Errors and edge cases
- Invalid input.
""",
    "SG004": """# Task
## Goal
Ship it.
## Expected result
A result.
## Acceptance criteria
- Given input, when run, then output exists.
## Errors and edge cases
- Invalid input.
""",
    "SG005": """# Task
## Goal
Ship it.
## Expected result
A result.
## Acceptance criteria
- Given input, when run, then output exists.
## Out of scope
None.
""",
    "SG101": VALID_SPEC + "\nMake it fast.\n",
    "SG102": VALID_SPEC.replace(
        "- Given 3 findings, when analysis runs, then the report contains 3 findings.",
        "- Export works fast.",
    ),
    "SG103": VALID_SPEC + "\n- Create report and add export.\n",
}


def _semantic_finding(finding: object) -> tuple[object, ...]:
    return (
        finding.rule_id,
        finding.severity,
        finding.message,
        finding.suggestion,
        finding.excerpt,
    )


@settings(max_examples=60, deadline=None)
@given(lines=TEXT_CASES, newline=NEWLINES)
def test_analysis_is_repeatable_for_arbitrary_unicode(lines: list[str], newline: str) -> None:
    text = newline.join(lines)
    first = analyze_text(text, source="generated.md")
    second = analyze_text(text, source="generated.md")
    assert first.to_dict() == second.to_dict()


@settings(max_examples=60, deadline=None)
@given(lines=TEXT_CASES)
def test_newline_encodings_are_semantically_equivalent(lines: list[str]) -> None:
    reports = [
        analyze_text(separator.join(lines), source="generated.md").to_dict()
        for separator in ("\n", "\r\n", "\r")
    ]
    assert reports[0] == reports[1] == reports[2]


@settings(max_examples=80, deadline=None)
@given(lines=TEXT_CASES, newline=NEWLINES)
def test_generated_findings_respect_public_contract(lines: list[str], newline: str) -> None:
    text = newline.join(lines)
    report = analyze_text(text, source="generated.md")
    document = Document.parse(text)

    assert report.source == "generated.md"
    for finding in report.findings:
        assert finding.rule_id in KNOWN_RULE_ID_SET
        assert finding.severity in SEVERITIES
        if finding.line is not None:
            assert 1 <= finding.line <= len(document.lines)


@settings(max_examples=60, deadline=None)
@given(rule_id=st.sampled_from(KNOWN_RULE_IDS), lines=TEXT_CASES)
def test_disabled_rule_never_emits_finding(rule_id: str, lines: list[str]) -> None:
    report = analyze_text(
        "\n".join(lines),
        config=ProjectConfig(rules={rule_id: RuleConfig(enabled=False)}),
    )
    assert rule_id not in {finding.rule_id for finding in report.findings}


@settings(max_examples=40, deadline=None)
@given(rule_id=st.sampled_from(KNOWN_RULE_IDS), severity=st.sampled_from(SEVERITIES))
def test_severity_override_changes_only_target_severity(
    rule_id: str,
    severity: Severity,
) -> None:
    text = TRIGGERS[rule_id]
    baseline = analyze_text(text)
    configured = analyze_text(
        text,
        config=ProjectConfig(rules={rule_id: RuleConfig(severity=severity)}),
    )

    baseline_target = [finding for finding in baseline.findings if finding.rule_id == rule_id]
    configured_target = [finding for finding in configured.findings if finding.rule_id == rule_id]
    assert baseline_target
    assert len(configured_target) == len(baseline_target)
    assert all(finding.severity is severity for finding in configured_target)

    baseline_identity = [
        (finding.rule_id, finding.message, finding.suggestion, finding.line, finding.excerpt)
        for finding in baseline.findings
    ]
    configured_identity = [
        (finding.rule_id, finding.message, finding.suggestion, finding.line, finding.excerpt)
        for finding in configured.findings
    ]
    assert configured_identity == baseline_identity


@settings(max_examples=40, deadline=None)
@given(rule_id=st.sampled_from(KNOWN_RULE_IDS))
def test_valid_file_suppression_never_creates_semantic_findings(rule_id: str) -> None:
    text = TRIGGERS[rule_id]
    baseline = analyze_text(text)
    suppressed = analyze_text(f"<!-- specgate-ignore-file {rule_id} -->\n{text}")

    assert rule_id not in {finding.rule_id for finding in suppressed.findings}
    baseline_semantics = Counter(_semantic_finding(finding) for finding in baseline.findings)
    suppressed_semantics = Counter(_semantic_finding(finding) for finding in suppressed.findings)
    assert suppressed_semantics <= baseline_semantics


@settings(max_examples=60, deadline=None)
@given(lines=TEXT_CASES, newline=NEWLINES)
def test_reporters_preserve_report_counts(lines: list[str], newline: str) -> None:
    report = analyze_text(newline.join(lines), source="generated.md")
    payload = json.loads(render_json(report))
    assert payload == report.to_dict()

    markdown = render_markdown(report)
    assert f"| Error | {report.count(Severity.ERROR)} |" in markdown
    assert f"| Warning | {report.count(Severity.WARNING)} |" in markdown
    assert f"| Info | {report.count(Severity.INFO)} |" in markdown
