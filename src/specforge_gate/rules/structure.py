"""Structural rules for software requirements."""

from __future__ import annotations

from dataclasses import dataclass

from specforge_gate.document import Document
from specforge_gate.models import Finding, Severity

_GOAL = ("goal", "objective", "цель", "задача")
_RESULT = ("expected result", "deliverable", "результат", "что должно получиться")
_ACCEPTANCE = (
    "acceptance criteria",
    "definition of done",
    "критерии приёмки",
    "критерии приемки",
    "условия приёмки",
)
_OUT_OF_SCOPE = ("out of scope", "non-goals", "не входит", "вне scope", "вне скоупа")
_NEGATIVE = (
    "error handling",
    "edge cases",
    "negative scenarios",
    "ошибки",
    "граничные случаи",
    "негативные сценарии",
)


@dataclass(frozen=True, slots=True)
class RequiredSectionRule:
    rule_id: str
    aliases: tuple[str, ...]
    title: str
    severity: Severity
    suggestion: str

    def check(self, document: Document) -> list[Finding]:
        section = document.find_section(self.aliases)
        if section is None or not section.body.strip():
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Missing or empty section: {self.title}.",
                    suggestion=self.suggestion,
                )
            ]
        return []


def structural_rules() -> tuple[RequiredSectionRule, ...]:
    return (
        RequiredSectionRule(
            "SG001",
            _GOAL,
            "Goal",
            Severity.ERROR,
            "State the user or business outcome in one or two sentences.",
        ),
        RequiredSectionRule(
            "SG002",
            _RESULT,
            "Expected result",
            Severity.ERROR,
            "Describe the concrete artifact, behavior, or state that must exist after delivery.",
        ),
        RequiredSectionRule(
            "SG003",
            _ACCEPTANCE,
            "Acceptance criteria",
            Severity.ERROR,
            "Add observable pass/fail criteria as a checklist or numbered list.",
        ),
        RequiredSectionRule(
            "SG004",
            _OUT_OF_SCOPE,
            "Out of scope",
            Severity.WARNING,
            "Explicitly list excluded capabilities to prevent scope expansion.",
        ),
        RequiredSectionRule(
            "SG005",
            _NEGATIVE,
            "Errors and edge cases",
            Severity.WARNING,
            "Describe invalid input, unavailable dependencies, permission failures, and boundaries.",
        ),
    )


ACCEPTANCE_ALIASES = _ACCEPTANCE
