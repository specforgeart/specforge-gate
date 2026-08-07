#!/usr/bin/env python3
"""Summarize mutmut 3.x metadata and enforce the accepted survivor baseline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

_STATUS_BY_EXIT_CODE: dict[int, str] = {
    0: "survived",
    1: "killed",
    2: "interrupted",
    3: "killed",
    5: "no_tests",
    24: "timeout",
    33: "no_tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    152: "timeout",
    255: "timeout",
    -24: "killed",
    -11: "segfault",
}


def collect_summary(mutants_root: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    meta_files = sorted(mutants_root.rglob("*.meta")) if mutants_root.exists() else []
    mutant_count = 0

    for meta_path in meta_files:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        exit_codes = data.get("exit_code_by_key", {})
        if not isinstance(exit_codes, dict):
            counts["invalid_meta"] += 1
            continue
        for exit_code in exit_codes.values():
            mutant_count += 1
            if exit_code is None:
                counts["not_checked"] += 1
            elif isinstance(exit_code, int):
                counts[_STATUS_BY_EXIT_CODE.get(exit_code, "other")] += 1
            else:
                counts["other"] += 1

    killed = counts["killed"]
    survived = counts["survived"]
    scored = killed + survived
    kill_rate = round((killed / scored) * 100, 2) if scored else None

    return {
        "meta_files": len(meta_files),
        "total_mutants": mutant_count,
        "killed": killed,
        "survived": survived,
        "no_tests": counts["no_tests"],
        "timeout": counts["timeout"],
        "suspicious": counts["suspicious"],
        "skipped": counts["skipped"],
        "segfault": counts["segfault"],
        "interrupted": counts["interrupted"],
        "not_checked": counts["not_checked"],
        "invalid_meta": counts["invalid_meta"],
        "other": counts["other"],
        "kill_rate_percent": kill_rate,
    }


def is_complete(summary: dict[str, Any]) -> bool:
    return bool(summary["meta_files"]) and not any(
        summary[key]
        for key in ("segfault", "interrupted", "not_checked", "invalid_meta", "other")
    )


def parse_survivor_ids(results_text: str) -> frozenset[str]:
    suffix = ": survived"
    return frozenset(
        line.strip()[: -len(suffix)]
        for line in results_text.splitlines()
        if line.strip().endswith(suffix)
    )


def load_allowed_survivors(path: Path) -> frozenset[str]:
    return frozenset(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def apply_survivor_baseline(
    summary: dict[str, Any],
    *,
    results_text: str,
    allowed_survivors: frozenset[str],
) -> None:
    actual = parse_survivor_ids(results_text)
    summary["accepted_survivors"] = sorted(actual & allowed_survivors)
    summary["unexpected_survivors"] = sorted(actual - allowed_survivors)
    summary["resolved_allowed_survivors"] = sorted(allowed_survivors - actual)


def render_markdown(summary: dict[str, Any], results_text: str = "") -> str:
    kill_rate = summary["kill_rate_percent"]
    kill_rate_text = "n/a" if kill_rate is None else f"{kill_rate:.2f}%"
    unexpected = summary.get("unexpected_survivors", [])
    accepted = summary.get("accepted_survivors", [])
    resolved = summary.get("resolved_allowed_survivors", [])
    lines = [
        "## Mutation testing",
        "",
        f"- Total mutants: **{summary['total_mutants']}**",
        f"- Killed: **{summary['killed']}**",
        f"- Survived: **{summary['survived']}**",
        f"- No tests: **{summary['no_tests']}**",
        f"- Timeout: **{summary['timeout']}**",
        f"- Suspicious: **{summary['suspicious']}**",
        f"- Skipped: **{summary['skipped']}**",
        f"- Kill rate (killed / (killed + survived)): **{kill_rate_text}**",
        f"- Complete: **{'yes' if is_complete(summary) else 'no'}**",
    ]
    if "unexpected_survivors" in summary:
        lines.extend(
            [
                f"- Accepted survivors still present: **{len(accepted)}**",
                f"- Accepted survivors resolved: **{len(resolved)}**",
                f"- Unexpected survivors: **{len(unexpected)}**",
            ]
        )
    if unexpected:
        lines.extend(["", "### Unexpected survivors", "", "```text", *unexpected, "```"])
    if results_text.strip():
        excerpt = "\n".join(results_text.strip().splitlines()[:120])
        lines.extend(
            ["", "### Surviving/actionable mutants", "", "```text", excerpt, "```"]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutants", type=Path, default=Path("mutants"))
    parser.add_argument("--results", type=Path)
    parser.add_argument("--allowed-survivors", type=Path)
    parser.add_argument("--github-summary", type=Path)
    parser.add_argument("--output", type=Path, default=Path("mutation-summary.json"))
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    summary = collect_summary(args.mutants)
    results_text = ""
    if args.results is not None and args.results.is_file():
        results_text = args.results.read_text(encoding="utf-8", errors="replace")

    if args.allowed_survivors is not None:
        allowed = load_allowed_survivors(args.allowed_survivors)
        apply_survivor_baseline(
            summary,
            results_text=results_text,
            allowed_survivors=allowed,
        )

    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    markdown = render_markdown(summary, results_text)
    if args.github_summary is not None:
        with args.github_summary.open("a", encoding="utf-8") as handle:
            handle.write(markdown)

    print(json.dumps(summary, sort_keys=True))
    if results_text.strip():
        print("--- mutmut results ---")
        print(results_text.rstrip())

    if args.require_complete and not is_complete(summary):
        return 1
    if summary.get("unexpected_survivors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
