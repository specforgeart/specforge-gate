"""Inline suppression directive parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass

_DIRECTIVE_RE = re.compile(
    r"^\s*<!--\s*(specgate-ignore-file|specgate-ignore-next-line)\b(.*?)-->\s*$",
    re.IGNORECASE,
)
_ANY_SPEC_GATE_RE = re.compile(r"^\s*<!--\s*specgate-", re.IGNORECASE)
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_ID_RE = re.compile(r"^[A-Z]+\d+$", re.IGNORECASE)


class SuppressionError(ValueError):
    """Raised when an inline suppression directive is invalid."""

    def __init__(self, message: str, *, line: int) -> None:
        super().__init__(message)
        self.line = line


@dataclass(frozen=True, slots=True)
class SuppressionData:
    file_rule_ids: frozenset[str]
    next_line_rule_ids: dict[int, frozenset[str]]

    def suppresses(self, rule_id: str, line: int | None) -> bool:
        normalized = rule_id.upper()
        if normalized in self.file_rule_ids:
            return True
        if line is None:
            return False
        return normalized in self.next_line_rule_ids.get(line, frozenset())


def parse_suppressions(text: str, *, known_rule_ids: set[str]) -> tuple[str, SuppressionData]:
    """Return text with directive lines blanked and validated suppression data."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    known = {rule_id.upper() for rule_id in known_rule_ids}
    sanitized = list(lines)
    file_ids: set[str] = set()
    next_ids: dict[int, set[str]] = {}
    pending_next: list[tuple[int, frozenset[str]]] = []
    in_fence = False
    seen_content = False

    for index, line in enumerate(lines, start=1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            seen_content = True
            continue
        if in_fence:
            continue

        match = _DIRECTIVE_RE.match(line)
        if match:
            name = match.group(1).casefold()
            ids = _parse_ids(match.group(2), line=index, known_rule_ids=known)
            if name == "specgate-ignore-file":
                if seen_content:
                    raise SuppressionError(
                        "ignore-file must appear in the document preamble", line=index
                    )
                file_ids.update(ids)
            else:
                pending_next.append((index, frozenset(ids)))
            sanitized[index - 1] = ""
            continue

        if _ANY_SPEC_GATE_RE.match(line):
            raise SuppressionError("malformed suppression directive", line=index)

        if not line.strip():
            continue

        if pending_next:
            for _, ids in pending_next:
                next_ids.setdefault(index, set()).update(ids)
            pending_next.clear()
        seen_content = True

    return "\n".join(sanitized), SuppressionData(
        file_rule_ids=frozenset(file_ids),
        next_line_rule_ids={line: frozenset(ids) for line, ids in next_ids.items()},
    )


def _parse_ids(raw: str, *, line: int, known_rule_ids: set[str]) -> frozenset[str]:
    stripped = raw.strip()
    if not stripped:
        raise SuppressionError("suppression directive requires at least one rule ID", line=line)
    parts = [part for part in re.split(r"[\s,]+", stripped) if part]
    ids = frozenset(part.upper() for part in parts)
    if not all(_ID_RE.match(part) for part in ids):
        raise SuppressionError("malformed suppression rule ID list", line=line)
    unknown = sorted(ids - known_rule_ids)
    if unknown:
        raise SuppressionError(f"unknown suppression rule ID: {', '.join(unknown)}", line=line)
    return ids
