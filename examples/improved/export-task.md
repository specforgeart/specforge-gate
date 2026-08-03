# Export audit report

## Goal
Allow an operator to export the current audit result for offline review.

## Expected result
A UTF-8 Markdown file containing the status summary and every finding shown in the UI.

## Scope
- Export the current in-memory report to Markdown.
- Preserve finding order and severity.

## Out of scope
- PDF export.
- Email delivery.
- Historical reports.

## Acceptance criteria
- Given a report with 3 findings, when export is requested, then one `.md` file contains all 3 findings.
- Given Cyrillic input, the exported file opens as UTF-8 without corrupted characters.
- For a report up to 1 MB, export completes within 2 seconds on the reference environment.

## Errors and edge cases
- If the target path is not writable, no partial file remains and the application returns an actionable error.
- If the report is empty, the file contains the PASS status and zero findings.
