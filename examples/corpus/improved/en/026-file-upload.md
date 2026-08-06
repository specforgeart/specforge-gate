# Project attachment upload

## Goal
Let a project member attach a document to a project record.

## Expected result
An accepted file appears once in the project attachment list with its original name.

## Out of scope
- Archive extraction.
- Virus remediation.
- Public file sharing.

## Acceptance criteria
- Given a PDF below 20 MB, when it is submitted, then 1 attachment record appears.
- Given a 21 MB file, when it is submitted, then the request is rejected.
- Given 2 files with the same name, when both are submitted, then 2 distinct attachment identifiers exist.

## Errors and edge cases
- Interrupted storage leaves no attachment record.
- Unsupported media types are rejected.
- A duplicate request identifier does not create a second record.
