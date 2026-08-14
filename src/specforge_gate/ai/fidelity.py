"""Deterministic fidelity checks for advisory AI-generated specification drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from .contradictions import Contradiction


class DraftFidelityStatus(StrEnum):
    """Safety status for an advisory improved-spec draft."""

    PASS = "PASS"
    UNSAFE = "UNSAFE"


@dataclass(frozen=True, slots=True)
class DraftFidelityFinding:
    """One deterministic indication that a draft may have invented requirements."""

    code: str
    message: str
    suggestion: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class DraftFidelityReport:
    """Deterministic fidelity report for one generated draft."""

    findings: tuple[DraftFidelityFinding, ...]

    @property
    def status(self) -> DraftFidelityStatus:
        return DraftFidelityStatus.PASS if not self.findings else DraftFidelityStatus.UNSAFE

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "summary": {"total": len(self.findings)},
            "findings": [item.to_dict() for item in self.findings],
        }


_ORDERED_LIST_PREFIX_RE = re.compile(r"(?m)^\s*\d+[.)]\s+")
_NUMBER_RE = re.compile(r"(?<![\w])\d(?:[\d,_ ]*\d)?(?:\.\d+)?")
_RESOLUTION_PATTERNS = (
    re.compile(
        r"(?i)\b(?:contradiction|conflict)\b[^\n.!?]{0,80}"
        r"\b(?:resolved|reconciled|eliminated)\b"
    ),
    re.compile(
        r"(?i)\b(?:resolved|reconciled|eliminated)\b[^\n.!?]{0,40}"
        r"\b(?:contradiction|conflict)\b"
    ),
    re.compile(
        r"(?i)\b(?:противореч\w*|конфликт\w*)\b[^\n.!?]{0,80}"
        r"\b(?:разреш\w*|реш[её]н\w*|устран\w*)\b"
    ),
    re.compile(
        r"(?i)\b(?:разреш\w*|реш[её]н\w*|устран\w*)\b[^\n.!?]{0,40}"
        r"\b(?:противореч\w*|конфликт\w*)\b"
    ),
)
_STRONG_CLAIM_RE = re.compile(
    r"(?i)\b(?:must|shall|required|prohibited|forbidden|never|always|"
    r"not\s+permitted|not\s+allowed|"
    r"должен|должна|должно|должны|обязан|обязана|обязано|обязаны|"
    r"запрещ\w*|не\s+допускается|не\s+долж\w*|никогда|всегда)\b"
)
_TODO_RE = re.compile(
    r"(?i)\b(?:todo|open\s+question|clarify|needs?\s+clarification|"
    r"уточн\w*|вопрос\w*|требует\s+уточнения)\b"
)
_MARKDOWN_PREFIX_RE = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)

_OUT_OF_SCOPE_HEADINGS = {
    "out of scope",
    "non-goals",
    "non goals",
    "вне рамок",
    "не входит в объем",
    "не входит в объём",
}

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "then",
    "this",
    "to",
    "when",
    "with",
    "must",
    "shall",
    "required",
    "prohibited",
    "forbidden",
    "never",
    "always",
    "not",
    "allowed",
    "permitted",
    "а",
    "без",
    "быть",
    "в",
    "для",
    "должен",
    "должна",
    "должно",
    "должны",
    "и",
    "из",
    "или",
    "к",
    "как",
    "на",
    "не",
    "но",
    "по",
    "при",
    "с",
    "то",
    "что",
}


def analyze_draft_fidelity(
    source: str,
    draft: str,
    *,
    contradictions: tuple[Contradiction, ...] = (),
) -> DraftFidelityReport:
    """Check a generated draft for high-confidence unsupported requirement changes."""
    _validate_input(source, "source")
    _validate_input(draft, "draft")
    if not isinstance(contradictions, tuple) or not all(
        isinstance(item, Contradiction) for item in contradictions
    ):
        raise ValueError("contradictions must be a tuple of Contradiction values")

    findings: list[DraftFidelityFinding] = []
    findings.extend(_new_numeric_findings(source, draft))
    findings.extend(_resolution_findings(source, draft, contradictions))
    findings.extend(_strong_claim_findings(source, draft))
    findings.extend(_out_of_scope_findings(source, draft))
    return DraftFidelityReport(findings=tuple(findings))


def _validate_input(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def _new_numeric_findings(source: str, draft: str) -> list[DraftFidelityFinding]:
    source_numbers = {normalized for normalized, _raw in _numeric_literals(source)}
    seen: set[str] = set()
    findings: list[DraftFidelityFinding] = []

    for normalized, raw in _numeric_literals(draft):
        if normalized in source_numbers or normalized in seen:
            continue
        seen.add(normalized)
        findings.append(
            DraftFidelityFinding(
                code="AIF001",
                message="Draft introduces a numeric literal that is absent from the source.",
                suggestion=(
                    "Remove the new number or replace the unsupported detail with an explicit TODO."
                ),
                evidence=raw,
            )
        )
    return findings


def _numeric_literals(text: str) -> list[tuple[str, str]]:
    without_list_numbers = _ORDERED_LIST_PREFIX_RE.sub("", text)
    result: list[tuple[str, str]] = []
    for match in _NUMBER_RE.finditer(without_list_numbers):
        raw = match.group(0).strip()
        normalized = raw.replace(",", "").replace("_", "").replace(" ", "")
        result.append((normalized, raw))
    return result


def _resolution_findings(
    source: str,
    draft: str,
    contradictions: tuple[Contradiction, ...],
) -> list[DraftFidelityFinding]:
    if not contradictions:
        return []

    source_folded = " ".join(source.casefold().split())
    findings: list[DraftFidelityFinding] = []
    seen: set[str] = set()

    for pattern in _RESOLUTION_PATTERNS:
        for match in pattern.finditer(draft):
            evidence = " ".join(match.group(0).split())
            folded = evidence.casefold()
            if folded in source_folded or folded in seen:
                continue
            seen.add(folded)
            findings.append(
                DraftFidelityFinding(
                    code="AIF002",
                    message="Draft claims an unresolved contradiction or conflict is resolved.",
                    suggestion=(
                        "Keep the conflict explicit and request a stakeholder decision instead."
                    ),
                    evidence=evidence,
                )
            )
    return findings


def _strong_claim_findings(source: str, draft: str) -> list[DraftFidelityFinding]:
    source_lines = [_clean_line(line) for line in source.splitlines()]
    source_lines = [line for line in source_lines if line]
    source_fragments = [_content_tokens(line) for line in source_lines]
    source_vocab: set[str] = set()
    for fragment in source_fragments:
        source_vocab.update(fragment)

    findings: list[DraftFidelityFinding] = []
    seen: set[str] = set()

    for raw_line in draft.splitlines():
        line = _clean_line(raw_line)
        if not line or _TODO_RE.search(line) or _STRONG_CLAIM_RE.search(line) is None:
            continue

        folded = " ".join(line.casefold().split())
        if folded in seen or _line_supported_verbatim(folded, source_lines):
            continue
        seen.add(folded)

        tokens = _content_tokens(line)
        if len(tokens) < 3:
            continue

        best_coverage = max(
            (len(tokens & fragment) / len(tokens) for fragment in source_fragments),
            default=0.0,
        )
        novel_tokens = tokens - source_vocab
        if best_coverage >= 0.55 or len(novel_tokens) < 2:
            continue

        findings.append(
            DraftFidelityFinding(
                code="AIF003",
                message=(
                    "Draft adds a strong requirement or prohibition without enough source evidence."
                ),
                suggestion=(
                    "Rewrite the claim as a TODO/open question unless the source explicitly "
                    "supports it."
                ),
                evidence=line,
            )
        )
    return findings


def _out_of_scope_findings(source: str, draft: str) -> list[DraftFidelityFinding]:
    source_items = _section_items(source, _OUT_OF_SCOPE_HEADINGS)
    draft_items = _section_items(draft, _OUT_OF_SCOPE_HEADINGS)
    if not source_items or not draft_items:
        return []

    source_tokens = [_content_tokens(item) for item in source_items]
    source_vocab: set[str] = set()
    for tokens in source_tokens:
        source_vocab.update(tokens)

    findings: list[DraftFidelityFinding] = []
    seen: set[str] = set()
    for item in draft_items:
        folded = " ".join(item.casefold().split())
        if folded in seen or _line_supported_verbatim(folded, source_items):
            continue
        seen.add(folded)

        tokens = _content_tokens(item)
        if len(tokens) < 2:
            continue
        best_coverage = max(
            (len(tokens & source_item) / len(tokens) for source_item in source_tokens),
            default=0.0,
        )
        novel_tokens = tokens - source_vocab
        if best_coverage >= 0.55 or len(novel_tokens) < 2:
            continue

        findings.append(
            DraftFidelityFinding(
                code="AIF004",
                message="Draft adds an out-of-scope constraint that is absent from the source.",
                suggestion=(
                    "Remove the new scope exclusion or convert it to an explicit open question."
                ),
                evidence=item,
            )
        )
    return findings


def _section_items(text: str, headings: set[str]) -> list[str]:
    active = False
    items: list[str] = []
    for raw_line in text.splitlines():
        heading = _HEADING_RE.match(raw_line)
        if heading:
            title = " ".join(heading.group(1).casefold().split())
            active = title in headings
            continue
        if not active:
            continue
        cleaned = _clean_line(raw_line)
        if cleaned:
            items.append(cleaned)
    return items


def _clean_line(line: str) -> str:
    cleaned = _MARKDOWN_PREFIX_RE.sub("", line).strip()
    return cleaned.replace("**", "").replace("__", "").strip()


def _line_supported_verbatim(line_folded: str, source_lines: list[str]) -> bool:
    return any(line_folded == " ".join(item.casefold().split()) for item in source_lines)


def _content_tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _WORD_RE.findall(text)
        if len(token) >= 2 and token.casefold() not in _STOP_WORDS
    }
