# API rate limit

## Goal
Protect the public API from request bursts above the configured client threshold.

## Expected result
Requests above the threshold receive HTTP 429 with a retry interval.

## Out of scope
- Billing limits.
- Global traffic shaping.
- User-interface throttling.

## Acceptance criteria
- Given 101 requests in 60 seconds and a limit of 100 requests, when request 101 arrives, then it receives HTTP 429.
- Given 100 requests in 60 seconds and a limit of 100 requests, when request 100 arrives, then it succeeds.
- Given a 60-second window reset, when the next request arrives, then the counter starts at 1 request.

## Errors and edge cases
- Missing client identity uses the anonymous-client bucket.
- Counter storage failure returns a service-unavailable response.
