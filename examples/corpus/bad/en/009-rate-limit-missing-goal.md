# API rate limit

## Expected result
Requests above the configured threshold receive HTTP 429.

## Out of scope
- Per-customer billing limits.

## Acceptance criteria
- Given 101 requests in 60 seconds, when the limit is 100 requests, then request 101 receives HTTP 429.
- Given 100 requests in 60 seconds, when the limit is 100 requests, then no request receives HTTP 429.

## Errors and edge cases
- Missing client identity uses the anonymous-client bucket.
