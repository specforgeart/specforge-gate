# Account export

## Objective
Give an account owner a portable copy of profile data.

## Deliverable
A UTF-8 JSON file contains the account profile and preferences.

## Non-goals
- Message history.
- Deleted records.

## Definition of done
- Given 2 preference records, when the export runs, then the JSON contains 2 preference objects.
- For a file up to 5 MB, generation completes within 10 seconds.

## Negative scenarios
- A storage failure returns no partial export.
