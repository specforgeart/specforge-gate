# Saved search filters

## Goal
Let an operator reuse a named set of search conditions.

## Expected result
Selecting a stored filter restores its field values on the search page.

## Out of scope
- Sharing filters between accounts.
- Automatic filter recommendations.

## Acceptance criteria
- Given a filter with 3 fields, when it is selected, then the form contains the same 3 values.
- Given a renamed filter, when the list opens, then the new name appears once.
- Given no stored filters, when the list opens, then an empty-state message appears.

## Errors and edge cases
- A deleted filter returns not found.
- An invalid field value is ignored and recorded.
