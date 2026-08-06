# File upload

## Goal
Provide a convenient file transfer for project attachments.

## Expected result
The upload finishes quickly and the attachment appears on the project.

## Out of scope
- Virus remediation.
- Archive extraction.

## Acceptance criteria
- Upload is fast.

## Errors and edge cases
- Files above 20 MB are rejected.
- Interrupted transfers leave no attachment record.
