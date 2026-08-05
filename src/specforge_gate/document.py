"""Lightweight Markdown/plain-text document model."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$")


@dataclass(frozen=True, slots=True)
class Section:
    title: str
    line: int
    body: str


@dataclass(frozen=True, slots=True)
class Document:
    text: str
    lines: tuple[str, ...]
    sections: tuple[Section, ...]

    @classmethod
    def parse(cls, text: str) -> Document:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = tuple(normalized.splitlines())
        headings: list[tuple[int, str]] = []
        for index, line in enumerate(lines, start=1):
            match = _HEADING_RE.match(line)
            if match:
                headings.append((index, match.group(2).strip()))

        sections: list[Section] = []
        for position, (line_number, title) in enumerate(headings):
            next_line = (
                headings[position + 1][0]
                if position + 1 < len(headings)
                else len(lines) + 1
            )
            body = "\n".join(lines[line_number: next_line - 1]).strip()
            sections.append(Section(title=title, line=line_number, body=body))

        return cls(text=normalized, lines=lines, sections=tuple(sections))

    def find_section(self, aliases: tuple[str, ...]) -> Section | None:
        lowered_aliases = tuple(alias.casefold() for alias in aliases)
        for section in self.sections:
            title = section.title.casefold()
            if any(alias in title for alias in lowered_aliases):
                return section
        return None

    def list_items(self, section: Section | None = None) -> tuple[tuple[int, str], ...]:
        start = 1
        end = len(self.lines)
        if section is not None:
            start = section.line + 1
            following = [item.line for item in self.sections if item.line > section.line]
            end = min(following) - 1 if following else len(self.lines)

        result: list[tuple[int, str]] = []
        for index in range(start, end + 1):
            match = _LIST_RE.match(self.lines[index - 1])
            if match:
                result.append((index, match.group(1).strip()))
        return tuple(result)
