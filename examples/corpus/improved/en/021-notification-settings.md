# Notification settings

## Goal
Let a user choose which account events produce email notifications.

## Expected result
Each supported event follows the saved enabled or disabled state.

## Out of scope
- SMS notifications.
- Marketing campaigns.
- Message-template editing.

## Acceptance criteria
- Given email alerts are disabled, when an account event occurs, then no email is queued.
- Given email alerts are enabled, when an account event occurs, then exactly 1 email is queued.
- Given 2 supported event types, when both settings are saved, then both values remain after reload.

## Errors and edge cases
- A rejected address records a delivery failure.
- A settings write failure preserves the previous values.
