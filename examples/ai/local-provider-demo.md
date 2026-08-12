# Goal

Allow an operator to export the currently filtered orders to a UTF-8 CSV file.

# Expected result

The downloaded CSV contains only orders matching the active filters and preserves non-ASCII names.

# Acceptance criteria

- Given filtered orders, when Export CSV is selected, then the downloaded CSV contains those rows.
- The export must complete within 2 seconds.
- The export may take up to 30 seconds.
- Given no matching orders, when export runs, then the CSV contains headers and no data rows.

# Out of scope

- XLSX export
- scheduled exports
- emailing export files

# Errors and edge cases

- empty result sets
- export-generation failure
- non-ASCII customer names
