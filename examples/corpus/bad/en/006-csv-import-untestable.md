# CSV customer import

## Goal
Let an operator load customer records from a CSV file.

## Expected result
Valid rows become customer records and rejected rows appear in an error report.

## Out of scope
- Spreadsheet formulas.
- XLSX files.

## Acceptance criteria
- The import is fast and easy.

## Errors and edge cases
- Invalid UTF-8 input returns an encoding error.
- Duplicate customer identifiers are rejected.
