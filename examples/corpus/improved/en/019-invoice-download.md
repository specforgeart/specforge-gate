# Invoice download

## Goal
Let an account owner retrieve an invoice for a completed billing period.

## Expected result
The selected invoice is returned as a PDF with its invoice number and line items.

## Out of scope
- Invoice editing.
- Tax-rule changes.
- Email delivery.

## Acceptance criteria
- Given invoice 42 with 5 line items, when its owner requests it, then the PDF contains invoice 42 and 5 items.
- Given an invoice from another account, when access is attempted, then the request is denied.
- For a PDF up to 2 MB, the response completes within 3 seconds.

## Errors and edge cases
- A missing invoice returns not found.
- A rendering failure returns no partial document.
