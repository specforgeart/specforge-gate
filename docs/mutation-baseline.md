# Mutation testing baseline

> **Status: REMEDIATION IN PROGRESS. DO NOT MERGE ISSUE #19 YET.**

The first GitHub-hosted Ubuntu mutation run completed successfully for PR #20. It established a clean tooling baseline and exposed meaningful survivor clusters that are being converted into explicit regression contracts before the final Issue #19 merge.

## Bootstrap measurement 1

- workflow run: `Mutation Testing` run `31174423523`;
- implementation head: `689c8883abffb6840549f23dc9ecd383b551ab6f`;
- Ubuntu runner: `ubuntu-24.04`;
- Python: `3.11.15`;
- mutmut: `3.7.0`;
- mutated files: `10`;
- total mutants: **478**;
- killed: **348**;
- survived: **130**;
- no tests: **0**;
- timeout: **0**;
- suspicious: **0**;
- skipped: **0**;
- incomplete/error states: **0**;
- kill rate `killed / (killed + survived)`: **72.80%**.

The run itself completed successfully. The absence of no-test, timeout, suspicious, interrupted, invalid-metadata, and other incomplete states means the 130 survivors are test-strength evidence rather than an incomplete mutation run.

## Survivor remediation

The first-pass survivors cluster around user-visible reporter formatting, analysis-engine copying/sorting/configuration behavior, configuration validation, suppression parsing, and structural-rule metadata/diagnostics.

The follow-up test pass therefore adds exact behavioral contracts for:

- text, JSON, and Markdown reporter output, including empty reports and non-ASCII JSON;
- engine suppression, severity override, copied findings, source preservation, and deterministic ordering;
- the structural rule registry, aliases, severities, suggestions, and missing-section diagnostics;
- suppression normalization, exact target-line mappings, case normalization, and validation errors;
- configuration validation errors and a full valid configuration mapping.

The temporary `pull_request` trigger remains enabled only while this remediation is measured. A second GitHub-hosted Ubuntu mutation run must complete after these tests are added. The final Issue #19 commit will then record the measured post-remediation result, classify any remaining meaningful survivors, remove the temporary PR trigger, and leave mutation testing schedule/manual only.

Mutation testing remains deliberately **outside** required `main` branch protection.
