# Administrative audit log

## Goal
Let an administrator review security-sensitive account changes.

## Expected result
The audit page lists timestamped events with actor, action, and target identifiers.

## Out of scope
- Editing audit events.
- Deleting audit events.
- Exporting the audit log.

## Acceptance criteria
- Given 25 events, when the page opens, then all 25 events are listed in descending time order.
- Given an unknown actor, when the page opens, then the actor is labeled unavailable.
- Given 101 events, when page 2 opens with a page size of 50 items, then 50 events are listed.

## Errors and edge cases
- A storage timeout returns an audit-data unavailable message.
- An event with missing optional metadata still appears.
