# CSV customer import

## Goal
Let an operator load customer records from a UTF-8 CSV file.

## Expected result
Valid rows become customer records and rejected rows appear in a row-level error report.

## Out of scope
- XLSX files.
- Spreadsheet formulas.
- Background scheduling.

## Acceptance criteria
- Given 100 valid rows, when the file is processed, then 100 customer records exist.
- Given 3 rejected rows, when processing finishes, then the error report contains 3 row numbers.
- For a file up to 10 MB, processing completes within 2 minutes.

## Errors and edge cases
- Invalid UTF-8 input returns an encoding error.
- Duplicate customer identifiers are rejected.
- A database failure commits no partial batch.
