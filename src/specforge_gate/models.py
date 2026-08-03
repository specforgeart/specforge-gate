"""Domain models for analysis results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Status(StrEnum):
    PASS = "PASS"
    NEEDS_WORK = "NEEDS WORK"


@dataclass(frozen=True, slots=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    suggestion: str
    line: int | None = None
    excerpt: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisReport:
    source: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def status(self) -> Status:
        return Status.PASS if not self.findings else Status.NEEDS_WORK

    def count(self, severity: Severity) -> int:
        return sum(item.severity == severity for item in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status.value,
            "summary": {
                "errors": self.count(Severity.ERROR),
                "warnings": self.count(Severity.WARNING),
                "info": self.count(Severity.INFO),
                "total": len(self.findings),
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }
