# Invoice download

## Goal
Let an account owner retrieve an invoice for a completed billing period.

## Expected result
The selected invoice is returned as a PDF document.

## Out of scope
- Invoice editing.
- Tax calculation changes.

## Acceptance criteria
- Given invoice 42, when the owner requests it, then invoice 42 is returned.
- Given another account, when access is attempted, then the request is denied.
