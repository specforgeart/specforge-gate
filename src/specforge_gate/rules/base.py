"""Rule protocol and helpers."""

from __future__ import annotations

from typing import Protocol

from specforge_gate.document import Document
from specforge_gate.models import Finding


class Rule(Protocol):
    rule_id: str

    def check(self, document: Document) -> list[Finding]: ...
