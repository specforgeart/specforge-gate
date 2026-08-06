# Cache cleanup

## Goal
Limit stale cache entries retained by the service.

## Expected result
Entries older than the configured age are removed from the cache.

## Out of scope
- Database record deletion.
- Cache-provider migration.

## Acceptance criteria
- 1000 expired items are removed within 30 seconds.
- Memory use remains below 500 MB during cleanup.
- The remaining cache contains 0 items older than 60 minutes.

## Errors and edge cases
- Provider unavailability leaves the existing cache unchanged.
- A retry starts from a fresh item listing.
