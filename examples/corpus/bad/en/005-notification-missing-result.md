# Notification preferences

## Goal
Let a user choose which account events produce email notifications.

## Out of scope
- SMS notifications.
- Marketing campaigns.

## Acceptance criteria
- Given email alerts are disabled, when an account event occurs, then no email is queued.
- Given email alerts are enabled, when an account event occurs, then one email is queued.

## Errors and edge cases
- A rejected email address records a delivery failure.
