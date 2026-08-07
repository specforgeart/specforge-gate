# Mutation testing baseline

> **Status: PENDING BOOTSTRAP MEASUREMENT. DO NOT MERGE THIS ISSUE UNTIL THIS FILE IS UPDATED WITH THE MEASURED GITHUB-HOSTED UBUNTU RESULT.**

Issue #19 introduces mutation testing as a separate deep-quality layer. The first measurement must come from the temporary pull-request bootstrap trigger in `.github/workflows/mutation-testing.yml` because mutmut 3.x requires POSIX `fork` support and cannot execute natively on Windows.

## Scope

The configured mutation source is `src/specforge_gate/`, excluding package metadata, CLI plumbing, and GitHub Action integration plumbing. The focused test selection covers the deterministic engine, configuration, suppression, rules, document parsing, reporters, and property-based invariants.

The run records these categories from mutmut metadata:

- killed;
- survived;
- no tests;
- timeout;
- suspicious;
- skipped;
- incomplete/error states.

The primary kill-rate metric is `killed / (killed + survived)`. `no tests`, timeout, and suspicious mutations are reported separately because they require different triage.

## Baseline procedure

1. Open the Issue #19 implementation pull request.
2. Wait for the non-required `Mutation Testing / mutation-testing` job to finish on GitHub-hosted Ubuntu.
3. Read the JSON summary from the job log and the surviving-mutant list emitted by `mutmut results`.
4. Classify every meaningful survivor/no-test/timeout/suspicious mutation.
5. Add or strengthen tests for real gaps; document only genuinely equivalent or tooling-artifact survivors.
6. Replace this pending section with the measured counts, kill rate, run URL, commit SHA, and survivor rationale.
7. Remove the temporary `pull_request` bootstrap trigger so permanent mutation testing is schedule/manual only.
8. Re-run the normal required pull-request gates before merge.

Mutation testing is deliberately **not** a required `main` branch-protection context. Its purpose is to measure test strength without making every pull request wait for the deep test layer.
