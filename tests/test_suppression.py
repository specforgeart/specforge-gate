from dataclasses import dataclass

import pytest

from specforge_gate.document import Document
from specforge_gate.engine import analyze_text
from specforge_gate.models import Finding, Severity
from specforge_gate.suppression import SuppressionError, parse_suppressions

VALID_SPEC = """# Task

## Goal
Ship it.

## Expected result
A result.

## Out of scope
None.

## Acceptance criteria
- Given input, when run, then output appears.

## Errors and edge cases
- Invalid input returns an error.
"""


def test_ignore_file_suppresses_space_separated_ids() -> None:
    report = analyze_text("<!-- specgate-ignore-file SG004 SG005 -->\n# Task\n")
    ids = {finding.rule_id for finding in report.findings}
    assert "SG004" not in ids
    assert "SG005" not in ids
    assert "SG001" in ids


def test_ignore_file_suppresses_comma_separated_ids() -> None:
    report = analyze_text("<!-- specgate-ignore-file SG004,SG005 -->\n# Task\n")
    assert {"SG004", "SG005"}.isdisjoint({finding.rule_id for finding in report.findings})


def test_ignore_file_suppresses_mixed_separators() -> None:
    report = analyze_text("<!-- specgate-ignore-file SG004, SG005 -->\n# Task\n")
    assert {"SG004", "SG005"}.isdisjoint({finding.rule_id for finding in report.findings})


def test_directives_are_case_insensitive() -> None:
    report = analyze_text("<!-- SPECGATE-IGNORE-FILE sg004 -->\n# Task\n")
    assert "SG004" not in {finding.rule_id for finding in report.findings}


def test_ignore_file_must_be_in_preamble() -> None:
    with pytest.raises(SuppressionError) as error:
        analyze_text("# Task\n<!-- specgate-ignore-file SG004 -->\n")
    assert error.value.line == 2


def test_ignore_next_line_suppresses_next_non_empty_line() -> None:
    report = analyze_text(
        VALID_SPEC + "\n<!-- specgate-ignore-next-line SG101 -->\n\nMake it fast.\n"
    )
    assert not [finding for finding in report.findings if finding.rule_id == "SG101"]


def test_ignore_next_line_does_not_suppress_later_lines() -> None:
    report = analyze_text(
        VALID_SPEC + "\n<!-- specgate-ignore-next-line SG101 -->\nOK.\nMake it fast.\n"
    )
    assert [finding for finding in report.findings if finding.rule_id == "SG101"]


def test_ignore_next_line_skips_directive_lines() -> None:
    report = analyze_text(
        VALID_SPEC
        + "\n<!-- specgate-ignore-next-line SG101 -->\n"
        + "<!-- specgate-ignore-next-line SG103 -->\nMake it fast.\n"
    )
    assert not [finding for finding in report.findings if finding.rule_id == "SG101"]


def test_ignore_file_preamble_allows_standalone_ordinary_html_comments() -> None:
    report = analyze_text(
        "<!-- ordinary project comment -->\n"
        "<!-- specgate-ignore-file SG004 -->\n"
        "# Task\n"
    )
    assert "SG004" not in {finding.rule_id for finding in report.findings}


def test_ignore_next_line_is_consumed_by_fenced_code_opener() -> None:
    report = analyze_text(
        VALID_SPEC
        + "\n<!-- specgate-ignore-next-line SG101 -->\n"
        + "```\n"
        + "code\n"
        + "```\n"
        + "Make it fast.\n"
    )
    assert [finding for finding in report.findings if finding.rule_id == "SG101"]


def test_ordinary_html_comment_consumes_pending_next_line_suppression() -> None:
    report = analyze_text(
        VALID_SPEC
        + "\n<!-- specgate-ignore-next-line SG101 -->\n"
        + "<!-- ordinary comment -->\n"
        + "Make it fast.\n"
    )
    assert [finding for finding in report.findings if finding.rule_id == "SG101"]


def test_tilde_marker_inside_backtick_fence_does_not_close_it() -> None:
    report = analyze_text(
        "```\n"
        "~~~\n"
        "<!-- specgate-ignore-file SG004 -->\n"
        "```\n"
        "# Task\n"
    )
    assert "SG004" in {finding.rule_id for finding in report.findings}


def test_backtick_marker_inside_tilde_fence_does_not_close_it() -> None:
    report = analyze_text(
        "~~~\n"
        "```\n"
        "<!-- specgate-ignore-file SG004 -->\n"
        "~~~\n"
        "# Task\n"
    )
    assert "SG004" in {finding.rule_id for finding in report.findings}


def test_shorter_backtick_marker_inside_longer_fence_does_not_close_it() -> None:
    report = analyze_text(
        "````\n"
        "```\n"
        "<!-- specgate-ignore-file SG004 -->\n"
        "````\n"
        "# Task\n"
    )
    assert "SG004" in {finding.rule_id for finding in report.findings}


def test_directives_inside_backtick_fences_are_ignored() -> None:
    report = analyze_text("```\n<!-- specgate-ignore-file SG004 -->\n```\n# Task\n")
    assert "SG004" in {finding.rule_id for finding in report.findings}


def test_directives_inside_tilde_fences_are_ignored() -> None:
    report = analyze_text("~~~\n<!-- specgate-ignore-file SG004 -->\n~~~\n# Task\n")
    assert "SG004" in {finding.rule_id for finding in report.findings}


def test_directive_lines_are_blanked_before_parsing() -> None:
    sanitized, _ = parse_suppressions(
        "<!-- specgate-ignore-file SG004 -->\n# Goal\n", known_rule_ids={"SG004"}
    )
    document = Document.parse(sanitized)
    assert document.lines[0] == ""
    assert document.sections[0].line == 2


def test_directive_does_not_count_as_section_body() -> None:
    sanitized, _ = parse_suppressions(
        "<!-- specgate-ignore-file SG004 -->\n"
        "## Goal\n"
        "<!-- specgate-ignore-next-line SG101 -->\n"
        "Make it fast.\n",
        known_rule_ids={"SG004", "SG101"},
    )
    document = Document.parse(sanitized)
    assert document.find_section(("goal",)).body == "Make it fast."


def test_unknown_id_raises_suppression_error() -> None:
    with pytest.raises(SuppressionError, match="unknown"):
        analyze_text("<!-- specgate-ignore-file SG999 -->\n# Task\n")


def test_malformed_directive_raises_suppression_error() -> None:
    with pytest.raises(SuppressionError, match="malformed"):
        analyze_text("<!-- specgate-ignore-later SG004 -->\n# Task\n")


def test_missing_ids_raises_suppression_error() -> None:
    with pytest.raises(SuppressionError, match="requires"):
        analyze_text("<!-- specgate-ignore-file -->\n# Task\n")


def test_partial_line_comment_is_not_a_directive() -> None:
    report = analyze_text(
        VALID_SPEC + "\nText <!-- specgate-ignore-next-line SG101 -->\nMake it fast.\n"
    )
    assert [finding for finding in report.findings if finding.rule_id == "SG101"]


@dataclass(frozen=True)
class CustomRule:
    rule_id: str = "XX001"

    def check(self, document: Document) -> list[Finding]:
        return [Finding(self.rule_id, Severity.ERROR, "custom", "fix", line=2, excerpt="bad")]


def test_custom_rule_ids_are_suppressible() -> None:
    report = analyze_text("<!-- specgate-ignore-next-line XX001 -->\nbad\n", rules=[CustomRule()])
    assert report.findings == []


def test_unsuppressed_custom_rule_is_reported() -> None:
    report = analyze_text("bad\n", rules=[CustomRule()])
    assert [finding.rule_id for finding in report.findings] == ["XX001"]


def test_file_suppression_removes_finding_before_counts() -> None:
    report = analyze_text("<!-- specgate-ignore-file SG001 SG002 SG003 -->\n# Task\n")
    assert report.count(Severity.ERROR) == 0


def test_severity_override_applies_to_unsuppressed_findings() -> None:
    from specforge_gate.config import ProjectConfig, RuleConfig

    report = analyze_text(
        "<!-- specgate-ignore-file SG004 -->\n# Task\nDo it fast.\n",
        config=ProjectConfig(rules={"SG101": RuleConfig(severity=Severity.ERROR)}),
    )
    assert next(f for f in report.findings if f.rule_id == "SG101").severity is Severity.ERROR
    assert "SG004" not in {finding.rule_id for finding in report.findings}


def test_unrecognized_html_comment_is_not_directive() -> None:
    report = analyze_text("<!-- note -->\n# Task\n")
    assert report.findings


def test_malformed_rule_id_raises_suppression_error() -> None:
    with pytest.raises(SuppressionError, match="malformed"):
        analyze_text("<!-- specgate-ignore-file SG-004 -->\n# Task\n")


def test_ignore_next_line_without_target_raises_suppression_error() -> None:
    with pytest.raises(SuppressionError) as error:
        analyze_text(VALID_SPEC + "\n<!-- specgate-ignore-next-line SG101 -->\n")
    assert error.value.line == 18


def test_suppressed_findings_are_absent_from_all_reporters() -> None:
    from specforge_gate.reporters import render_json, render_markdown, render_text

    report = analyze_text(
        "<!-- specgate-ignore-file SG001 SG002 SG003 SG004 SG005 SG101 -->\n"
        "# Task\n\nMake it fast.\n"
    )

    assert report.findings == []
    assert "PASS" in render_text(report)
    assert "SG101" not in render_text(report)
    assert '"status": "PASS"' in render_json(report)
    assert '"total": 0' in render_json(report)
    assert "SG101" not in render_json(report)
    assert "SpecForge Gate: PASS" in render_markdown(report)
    assert "SG101" not in render_markdown(report)
