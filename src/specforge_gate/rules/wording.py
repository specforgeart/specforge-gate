"""Rules for vague and untestable wording."""

from __future__ import annotations

import re
from dataclasses import dataclass

from specforge_gate.document import Document
from specforge_gate.models import Finding, Severity
from specforge_gate.rules.structure import ACCEPTANCE_ALIASES

_VAGUE_TERMS = (
    "fast",
    "quickly",
    "user-friendly",
    "convenient",
    "normal",
    "properly",
    "as needed",
    "if necessary",
    "efficient",
    "быстро",
    "удобно",
    "нормально",
    "корректно",
    "качественно",
    "при необходимости",
    "по возможности",
    "оперативно",
)

_MEASURABLE_RE = re.compile(
    r"(?:\b\d+(?:[.,]\d+)?\s*(?:ms|s|sec|seconds?|minutes?|%|mb|gb|items?|requests?|"
    r"мс|сек(?:унд[аы]?)?|мин(?:ут[аы]?)?|%|мб|гб|запрос(?:ов|а)?|элемент(?:ов|а)?)\b|"
    r"\b(?:given|when|then|допустим|когда|тогда)\b)",
    re.IGNORECASE,
)

_COMPOUND_RE = re.compile(r"\b(?:and|и|а также|plus|also)\b", re.IGNORECASE)
_ACTION_RE = re.compile(
    r"\b(?:create|add|implement|support|display|send|save|upload|download|"
    r"создать|добавить|реализовать|поддержать|показать|отправить|сохранить|загрузить|скачать)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class VagueWordingRule:
    rule_id: str = "SG101"

    def check(self, document: Document) -> list[Finding]:
        findings: list[Finding] = []
        for number, line in enumerate(document.lines, start=1):
            lowered = line.casefold()
            for term in _VAGUE_TERMS:
                if term.casefold() in lowered:
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=Severity.WARNING,
                            message=f"Vague wording: ‘{term}’.",
                            suggestion=(
                                "Replace it with an observable threshold, condition, "
                                "or example."
                            ),
                            line=number,
                            excerpt=line.strip(),
                        )
                    )
                    break
        return findings


@dataclass(frozen=True, slots=True)
class UntestableAcceptanceRule:
    rule_id: str = "SG102"

    def check(self, document: Document) -> list[Finding]:
        section = document.find_section(ACCEPTANCE_ALIASES)
        if section is None:
            return []

        findings: list[Finding] = []
        for line, item in document.list_items(section):
            if not _MEASURABLE_RE.search(item) and any(
                token in item.casefold()
                for token in ("fast", "easy", "correct", "быстр", "удоб", "коррект", "работает")
            ):
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.ERROR,
                        message="Acceptance criterion is not objectively testable.",
                        suggestion=(
                            "Define inputs, expected output, threshold, "
                            "or Given/When/Then behavior."
                        ),
                        line=line,
                        excerpt=item,
                    )
                )
        return findings


@dataclass(frozen=True, slots=True)
class CompoundRequirementRule:
    rule_id: str = "SG103"

    def check(self, document: Document) -> list[Finding]:
        findings: list[Finding] = []
        for line, item in document.list_items():
            if len(_ACTION_RE.findall(item)) >= 2 and _COMPOUND_RE.search(item):
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.INFO,
                        message="The item appears to contain multiple independent requirements.",
                        suggestion=(
                            "Split it into atomic requirements that can be "
                            "accepted separately."
                        ),
                        line=line,
                        excerpt=item,
                    )
                )
        return findings
