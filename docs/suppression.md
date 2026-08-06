# Inline rule suppression

SpecForge Gate supports narrow, explicit HTML comment directives for documented exceptions in a single source file.

## Syntax

```markdown
<!-- specgate-ignore-file SG004 SG005 -->
<!-- specgate-ignore-next-line SG101 -->
```

Rule IDs may be separated by spaces, commas, or both. Directive names and rule IDs are case-insensitive.

## Behavior

- Directives must be standalone full-line HTML comments.
- `specgate-ignore-file` applies to every finding with the listed IDs in that document and must appear in the document preamble, before the first non-empty content line.
- `specgate-ignore-next-line` applies to the next non-empty, non-directive physical line.
- Comments inside backtick or tilde fenced code blocks are treated as ordinary code, not directives.
- Recognized directive lines are blanked before parsing, preserving physical line numbers without making directives count as document content.
- Unknown rule IDs and malformed directives are invalid. The CLI reports the path and directive line, exits with code `2`, and does not print a traceback.

Suppressions are applied before reporting, counters, and exit-status evaluation. Severity overrides still apply to findings that are not suppressed.

## Out of scope

Region directives, wildcard suppression, suppression reasons, and suppression metadata are not supported.
