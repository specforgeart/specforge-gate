# Password reset

## Goal
Let a verified account owner replace a forgotten password.

## Expected result
A single-use link accepts a new password for the matching account.

## Out of scope
- Recovery without access to the registered email address.
- Administrator-initiated password changes.

## Acceptance criteria
- Given a valid token, when a 12-character password is submitted, then the password hash changes once.
- Given an expired token, when a password is submitted, then the request is rejected.
- Given a used token, when it is submitted again, then the request is rejected.

## Errors and edge cases
- Email delivery failure records a retryable delivery state.
- Token lookup failure changes no password.
