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

## Bootstrap measurement 2

The survivor-contract pass was measured on the second GitHub-hosted Ubuntu run:

- workflow run: `Mutation Testing` run `31177397007`;
- implementation head: `d54b98d836bc8152a6bf6026a909f4c4d733a643`;
- Ubuntu runner: `ubuntu-24.04`;
- Python: `3.11.15`;
- mutmut: `3.7.0`;
- mutated files: `10`;
- focused clean tests: **86 passed**;
- total mutants: **495**;
- killed: **471**;
- survived: **24**;
- no tests: **0**;
- timeout: **0**;
- suspicious: **0**;
- skipped: **0**;
- incomplete/error states: **0**;
- kill rate `killed / (killed + survived)`: **95.15%**.

This reduced survivors from **130 to 24** while keeping the mutation run complete. The
remaining survivors are distributed across reporters (1), engine (5), configuration
(3), and suppression parsing (15). A numeric score alone is not used to waive them.

## Remaining survivor classification

The result list identifies mutant IDs but does not by itself show whether a survivor is
meaningful or behaviorally equivalent. The temporary PR trigger therefore remains for
one diagnostic pass that records the exact source diff of every surviving mutant using
`mutmut apply` followed by `git diff`, restoring the source after each inspection.

The final Issue #19 commit will use those exact diffs to kill meaningful survivors with
regression tests or document equivalent/non-actionable survivors with rationale. It will
then remove the temporary `pull_request` trigger and leave mutation testing schedule/manual
only.

Mutation testing remains deliberately **outside** required `main` branch protection.

## Diagnostic measurement 3

The diagnostic GitHub-hosted Ubuntu run completed successfully without changing the
mutation score, as expected, because it added observability rather than behavioral tests:

- workflow run: `Mutation Testing` run `31180007212`;
- implementation head: `e39a6f953a19e2e0db40b2eb4c9a5ce8e2ee071d`;
- Ubuntu runner: `ubuntu-24.04`;
- Python: `3.11.15`;
- mutmut: `3.7.0`;
- focused clean tests: **86 passed**;
- total mutants: **495**;
- killed: **471**;
- survived: **24**;
- kill rate: **95.15%**;
- no-test, timeout, suspicious, skipped, and incomplete/error states: **0**.

The diagnostic step successfully applied every survivor one at a time, emitted its exact
`git diff`, restored `src/specforge_gate`, and finished with a clean product source tree.

### Meaningful survivors targeted by the final remediation pass

The exact diffs show **15 behavior-changing survivors** that should be killed by explicit
regression contracts:

- engine: default `source` mutation variants, `continue` -> `break` after a suppressed
  finding, and loss of numeric line ordering;
- suppression: lone-CR replacement corruption, equal-length fence-closing behavior,
  control-flow breaks inside/opening fenced blocks, pending-next suppression targeting
  a fence opener, preamble state after fenced content, malformed-directive message/line,
  and canonical multi-ID error formatting.

The remediation tests added after this diagnostic run directly exercise those behaviors.

### Survivors accepted as equivalent or mutation-environment-equivalent

Nine survivors are not useful targets for extra behavioral tests:

- `reporters.x_render_json__mutmut_2`: `ensure_ascii=False` -> `None`; both are falsey
  and produce the same `json.dumps` behavior.
- `engine.x_analyze_text__mutmut_44`: `item.line or 0` -> `item.line or 1`; valid finding
  lines are positive integers or `None`, and the preceding `item.line is None` key keeps
  `None` findings in a separate ordering bucket.
- `config.x_load_project_config__mutmut_8`: explicit UTF-8 -> platform default encoding.
  This is intentionally retained for cross-platform correctness, but Ubuntu's default
  encoding is UTF-8, so the mutation is behaviorally indistinguishable on the mutation
  runner. White-box assertions on the exact `Path.read_text` argument are deliberately
  avoided.
- `config.x_load_project_config__mutmut_10`: `utf-8` -> `UTF-8`; Python treats these as
  the same codec alias.
- `config.x__validate_config__mutmut_111`: omission of `version=version`; validation
  accepts only version `1`, which is also `ProjectConfig`'s default.
- `suppression.x_parse_suppressions__mutmut_12`: removing explicit lone-CR replacement;
  `str.splitlines()` already recognizes lone CR boundaries before sanitized text is
  rejoined with LF.
- `suppression.x_parse_suppressions__mutmut_23`: `seen_content=False` -> `None`; before
  assignment to `True`, the value is used only as a falsey preamble-state flag.
- `suppression.x_parse_suppressions__mutmut_38` and `__mutmut_52`: fence marker
  `marker[0]` -> `marker[1]`; `_FENCE_RE` permits only homogeneous runs of backticks or
  tildes, so those characters are necessarily identical.

These survivors are documented rather than hidden with implementation-coupled tests.
After the remediation measurement confirms the meaningful mutations are killed, the
temporary PR trigger and diagnostic diff step will be removed in the final cleanup commit.
