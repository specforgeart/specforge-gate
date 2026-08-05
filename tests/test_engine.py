from specforge_gate import Severity, Status, analyze_text

GOOD_SPEC = """# Export audit report

## Goal
Allow an operator to export the current audit result for review.

## Expected result
A UTF-8 Markdown file containing the summary and all findings.

## Scope
- Export the current in-memory report.

## Out of scope
- PDF export.
- Report history.

## Acceptance criteria
- Given 3 findings, when export is requested, then one `.md` file contains all findings.
- For a 1 MB report, export completes within 2 seconds.

## Errors and edge cases
- If the target path is not writable, no partial file remains and an error is returned.
"""


def test_good_spec_passes() -> None:
    report = analyze_text(GOOD_SPEC)
    assert report.status is Status.PASS
    assert report.findings == []


def test_missing_sections_are_reported() -> None:
    report = analyze_text("# Add export\n\nMake it convenient and fast.\n")
    ids = {finding.rule_id for finding in report.findings}
    assert {"SG001", "SG002", "SG003", "SG004", "SG005", "SG101"} <= ids
    assert report.count(Severity.ERROR) == 3


def test_untestable_acceptance_criterion_is_error() -> None:
    report = analyze_text(
        """# Task
## Goal
Export results.
## Expected result
A file.
## Out of scope
PDF.
## Errors and edge cases
No disk space.
## Acceptance criteria
- Export works correctly and fast.
"""
    )
    assert any(item.rule_id == "SG102" for item in report.findings)
