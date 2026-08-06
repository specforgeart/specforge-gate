# Administrative audit log

## Goal
Let an administrator review security-sensitive account changes.

## Expected result
The audit page lists timestamped events with actor and target identifiers.

## Out of scope

## Acceptance criteria
- Given 25 events, when the page opens, then all 25 events are listed.
- Given an unknown actor, when the page opens, then the actor is labeled as unavailable.

## Errors and edge cases
- A storage timeout returns an audit-data unavailable message.
