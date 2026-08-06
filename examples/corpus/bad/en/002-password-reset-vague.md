# Password reset

## Goal
Allow a user to regain account access after forgetting a password.

## Expected result
A reset link changes the password for the matching account.

## Out of scope
- Account recovery without email access.

## Acceptance criteria
- The reset flow is fast and easy.

## Errors and edge cases
- An expired token returns an expiration error.
