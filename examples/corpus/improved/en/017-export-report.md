# Export audit report

## Goal
Allow an operator to export the current audit result for offline review.

## Expected result
A UTF-8 Markdown file contains the status summary and every finding.

## Out of scope
- PDF export.
- Email delivery.
- Historical reports.

## Acceptance criteria
- Given a report with 3 findings, when export is requested, then one Markdown file contains all 3 findings.
- Given Cyrillic input, when the file opens, then all characters remain UTF-8.
- For a report up to 1 MB, export completes within 2 seconds.

## Errors and edge cases
- A non-writable target leaves no partial file.
- An empty report produces PASS with zero findings.
