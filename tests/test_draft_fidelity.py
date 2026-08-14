from __future__ import annotations

import pytest

from specforge_gate.ai import (
    Contradiction,
    DraftFidelityStatus,
    analyze_draft_fidelity,
)

SOURCE = """# Goal
Allow an operator to export filtered orders to UTF-8 CSV.

# Acceptance criteria
- The export must complete within 2 seconds under normal conditions.
- The export may take up to 30 seconds.

# Out of scope
- XLSX export
- scheduled exports

# Errors and edge cases
- empty result sets
- export-generation failure
"""

CONTRADICTION = Contradiction(
    statement_a="The export must complete within 2 seconds under normal conditions.",
    statement_b="The export may take up to 30 seconds.",
    explanation="The time limits conflict.",
)


def test_safe_todo_draft_passes_fidelity_guard() -> None:
    draft = """# Goal
Allow an operator to export filtered orders to UTF-8 CSV.

# Expected result
TODO: confirm the exact downloaded-file behavior.

# Acceptance criteria
- The export must complete within 2 seconds under normal conditions.
- The export may take up to 30 seconds.
- TODO: clarify which time limit is authoritative.

# Out of scope
- XLSX export
- scheduled exports

# Errors and edge cases
- empty result sets
- TODO: define behavior for export-generation failure.
"""

    report = analyze_draft_fidelity(
        SOURCE,
        draft,
        contradictions=(CONTRADICTION,),
    )

    assert report.status is DraftFidelityStatus.PASS
    assert report.findings == ()
    assert report.to_dict() == {
        "status": "PASS",
        "summary": {"total": 0},
        "findings": [],
    }


def test_acceptance_hallucinations_are_blocked_deterministically() -> None:
    draft = """# Goal
Enable efficient export of filtered orders.

# Acceptance criteria
- The export must complete within 2 seconds for datasets with <=10,000 rows.
- The export may take up to 30 seconds for datasets with >10,000 rows.
- If export-generation fails, the system must display an error message and prevent file download.

# Out of scope
- XLSX export
- scheduled exports
- Integration with third-party export tools

# Notes
- Contradiction resolved: the 2-second limit applies to small datasets.
- All exports must use UTF-8 encoding; legacy encoding options are prohibited.
- TODO: clarify behavior for datasets between 10,000 and 30,000 rows.
"""

    report = analyze_draft_fidelity(
        SOURCE,
        draft,
        contradictions=(CONTRADICTION,),
    )

    assert report.status is DraftFidelityStatus.UNSAFE
    codes = [item.code for item in report.findings]
    assert "AIF001" in codes
    assert "AIF002" in codes
    assert "AIF003" in codes
    assert "AIF004" in codes

    numeric_evidence = {
        item.evidence for item in report.findings if item.code == "AIF001"
    }
    assert "10,000" in numeric_evidence
    assert "30,000" in numeric_evidence
    assert any(
        "Contradiction resolved" in item.evidence for item in report.findings
    )
    assert any(
        "third-party export tools" in item.evidence for item in report.findings
    )


def test_ordered_markdown_list_numbers_do_not_count_as_new_numeric_requirements() -> None:
    source = """# Goal
Export CSV.
"""
    draft = """# Goal
Export CSV.

# Notes
1. TODO: clarify format.
2. TODO: clarify owner.
"""

    report = analyze_draft_fidelity(source, draft)

    assert report.status is DraftFidelityStatus.PASS



def test_markdown_prefix_parsing_handles_large_leading_whitespace() -> None:
    padding = " " * 20_000
    source = """# Goal
Export CSV.

# Out of scope
- XLSX export.
"""
    draft = (
        "# Goal\n"
        "Export CSV.\n\n"
        "# Out of scope\n"
        f"{padding}- XLSX export.\n\n"
        "# Notes\n"
        f"{padding}1. TODO: clarify owner.\n"
    )

    report = analyze_draft_fidelity(source, draft)

    assert report.status is DraftFidelityStatus.PASS


@pytest.mark.parametrize("value", ["", "   ", None, 123])
def test_invalid_source_or_draft_is_rejected(value: object) -> None:
    valid = """# Goal
Valid
"""
    with pytest.raises(ValueError):
        analyze_draft_fidelity(value, valid)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        analyze_draft_fidelity(valid, value)  # type: ignore[arg-type]


def test_contradictions_must_be_tuple_of_domain_values() -> None:
    source = """# Goal
Source
"""
    draft = """# Goal
Draft
"""
    with pytest.raises(ValueError, match="tuple of Contradiction"):
        analyze_draft_fidelity(
            source,
            draft,
            contradictions=[],  # type: ignore[arg-type]
        )
