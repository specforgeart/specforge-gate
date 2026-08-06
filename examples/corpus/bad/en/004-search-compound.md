# Saved search filters

## Goal
Let an operator reuse a previously selected search filter.

## Expected result
The chosen filter values are restored for the current search page.

## Scope
- Display saved filters and save the selection.

## Out of scope
- Sharing filters between accounts.

## Acceptance criteria
- Given one stored filter, when it is selected, then its field values appear.

## Errors and edge cases
- A deleted filter returns a not-found message.
