"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from specforge_gate.config import ConfigError, load_project_config
from specforge_gate.engine import analyze_text
from specforge_gate.models import AnalysisReport, Severity, Status
from specforge_gate.reporters import render_json, render_markdown, render_text
from specforge_gate.suppression import SuppressionError

_RENDERERS = {"text": render_text, "json": render_json, "markdown": render_markdown}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specgate", description="Lint software requirements.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Analyze Markdown/text files or directories.")
    check.add_argument("paths", nargs="+", type=Path)
    check.add_argument("--format", choices=tuple(_RENDERERS), default="text")
    check.add_argument(
        "--config",
        type=Path,
        help="Path to a .specgate.yml project configuration file.",
    )
    check.add_argument(
        "--fail-on",
        choices=("none", "warning", "error"),
        default="error",
        help="Return exit code 1 when findings at this level are present.",
    )

    ai_review = subparsers.add_parser(
        "ai-review",
        help="Run deterministic checks plus explicit advisory AI review for one file.",
    )
    ai_review.add_argument("path", type=Path)
    ai_review.add_argument("--format", choices=tuple(_RENDERERS), default="text")
    ai_review.add_argument(
        "--config",
        type=Path,
        help="Path to a .specgate.yml project configuration file.",
    )
    ai_review.add_argument(
        "--fail-on",
        choices=("none", "warning", "error"),
        default="error",
        help="Return exit code 1 when deterministic findings at this level are present.",
    )
    return parser


def _should_fail(fail_on: str, errors: int, warnings: int) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "warning":
        return errors + warnings > 0
    return errors > 0


def _json_unicode_escape(char: str) -> str:
    codepoint = ord(char)
    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04x}"
    value = codepoint - 0x10000
    high = 0xD800 + (value >> 10)
    low = 0xDC00 + (value & 0x3FF)
    return f"\\u{high:04x}\\u{low:04x}"


def _encoding_safe_output(text: str, encoding: str | None) -> str:
    if not encoding:
        return text
    try:
        text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        parts: list[str] = []
        for char in text:
            try:
                char.encode(encoding)
            except (LookupError, UnicodeEncodeError):
                parts.append(_json_unicode_escape(char))
            else:
                parts.append(char)
        return "".join(parts)
    return text


def _print_stdout(text: str) -> None:
    print(_encoding_safe_output(text, sys.stdout.encoding))


def _expand_paths(paths: list[Path]) -> list[tuple[Path, bool]]:
    expanded: list[tuple[Path, bool]] = []
    for path in paths:
        if path.is_dir():
            expanded.extend((item, True) for item in _discover_input_files(path))
        else:
            expanded.append((path, False))
    return sorted(expanded, key=lambda item: item[0].as_posix())


def _discover_input_files(directory: Path) -> tuple[Path, ...]:
    suffixes = {".md", ".markdown", ".txt"}
    return tuple(
        sorted(
            (item for item in directory.rglob("*") if item.is_file() and item.suffix in suffixes),
            key=lambda item: item.as_posix(),
        )
    )


def _render_output(
    format_name: str, reports: list[AnalysisReport], *, force_multi: bool = False
) -> str:
    if len(reports) == 1 and not force_multi:
        return _RENDERERS[format_name](reports[0])
    if format_name == "json":
        return _render_json_reports(reports)
    if format_name == "markdown":
        return _render_markdown_reports(reports)
    return _render_text_reports(reports)


def _render_text_reports(reports: list[AnalysisReport]) -> str:
    if not reports:
        return "PASS\n\nErrors: 0\nWarnings: 0\nInfo: 0"
    return "\n\n".join(f"== {report.source} ==\n{render_text(report)}" for report in reports)


def _render_markdown_reports(reports: list[AnalysisReport]) -> str:
    if not reports:
        return "# SpecForge Gate: PASS\n"
    return "\n".join(
        f"## `{report.source}`\n\n{render_markdown(report)}" for report in reports
    ).rstrip() + "\n"


def _render_json_reports(reports: list[AnalysisReport]) -> str:
    import json

    errors = sum(report.count(Severity.ERROR) for report in reports)
    warnings = sum(report.count(Severity.WARNING) for report in reports)
    info = sum(report.count(Severity.INFO) for report in reports)
    status = (
        Status.PASS.value
        if not errors and not warnings and not info
        else Status.NEEDS_WORK.value
    )
    payload = {
        "status": status,
        "summary": {
            "files": len(reports),
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "total": errors + warnings + info,
        },
        "reports": [report.to_dict() for report in reports],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _run_ai_review(args: argparse.Namespace) -> int:
    from specforge_gate.ai import (
        AIProviderError,
        ContradictionAnalysisError,
        ImprovedSpecDraftError,
        analyze_contradictions,
        draft_improved_specification,
    )
    from specforge_gate.ai.runtime import provider_from_environment

    try:
        config = load_project_config(args.config)
    except ConfigError as exc:
        print(f"specgate: {exc}", file=sys.stderr)
        return 2

    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"specgate: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    try:
        report = analyze_text(text, source=str(args.path), config=config)
    except SuppressionError as exc:
        print(f"specgate: {args.path}:{exc.line}: {exc}", file=sys.stderr)
        return 2

    try:
        provider = provider_from_environment()
        if provider is None:
            print(
                "specgate: AI provider is not configured. "
                "Set SPECFORGE_AI_PROVIDER and SPECFORGE_AI_MODEL.",
                file=sys.stderr,
            )
            return 2

        contradictions = analyze_contradictions(text, provider)
        draft = draft_improved_specification(
            text,
            provider,
            contradictions=contradictions.contradictions,
            findings=tuple(report.findings),
        )
    except AIProviderError as exc:
        print(
            f"specgate: AI provider {exc.provider} [{exc.code.value}]: {exc}",
            file=sys.stderr,
        )
        return 2
    except (ContradictionAnalysisError, ImprovedSpecDraftError) as exc:
        print(f"specgate: AI review [{exc.code.value}]: {exc}", file=sys.stderr)
        return 2

    try:
        draft_report = analyze_text(
            draft.text,
            source=f"{args.path}#improved-draft",
            config=config,
        )
    except SuppressionError as exc:
        print(
            f"specgate: AI draft deterministic recheck failed at line {exc.line}: {exc}",
            file=sys.stderr,
        )
        return 2

    if contradictions.provider != provider.provider_id or draft.provider != provider.provider_id:
        print("specgate: AI review provider identity mismatch.", file=sys.stderr)
        return 2

    payload: dict[str, Any] = {
        "deterministic": report.to_dict(),
        "draft_deterministic": draft_report.to_dict(),
        "provider": provider.provider_id,
        "model": provider.model,
        "contradictions": [
            {
                "statement_a": item.statement_a,
                "statement_b": item.statement_b,
                "explanation": item.explanation,
            }
            for item in contradictions.contradictions
        ],
        "improved_spec": draft.text,
    }
    _print_stdout(_render_ai_review(args.format, payload))

    errors = report.count(Severity.ERROR)
    warnings = report.count(Severity.WARNING)
    return int(_should_fail(args.fail_on, errors, warnings))


def _render_ai_review(format_name: str, payload: dict[str, Any]) -> str:
    if format_name == "json":
        import json

        return json.dumps(payload, ensure_ascii=False, indent=2)
    if format_name == "markdown":
        return _render_ai_review_markdown(payload)
    return _render_ai_review_text(payload)


def _safe_display_text(value: object) -> str:
    text = str(value)
    return "".join(
        char
        if char == "\n" or char == "\t" or (ord(char) >= 32 and ord(char) != 127)
        else f"\\u{ord(char):04x}"
        for char in text
    )


def _render_ai_review_text(payload: dict[str, Any]) -> str:
    report = payload["deterministic"]
    draft_report = payload["draft_deterministic"]
    summary = report["summary"]
    draft_summary = draft_report["summary"]
    contradictions = payload["contradictions"]
    lines = [
        "AI REVIEW",
        "",
        f"Provider: {_safe_display_text(payload['provider'])}",
        f"Model: {_safe_display_text(payload['model'])}",
        f"Deterministic: {_safe_display_text(report['status'])}",
        (
            "Findings: "
            f"{summary['errors']} errors, "
            f"{summary['warnings']} warnings, "
            f"{summary['info']} info"
        ),
        f"Contradictions: {len(contradictions)}",
        f"Draft gate: {_safe_display_text(draft_report['status'])}",
        (
            "Draft findings: "
            f"{draft_summary['errors']} errors, "
            f"{draft_summary['warnings']} warnings, "
            f"{draft_summary['info']} info"
        ),
    ]
    for index, item in enumerate(contradictions, start=1):
        lines.extend(
            [
                "",
                f"[{index}] {_safe_display_text(item['statement_a'])}",
                f"vs. {_safe_display_text(item['statement_b'])}",
                _safe_display_text(item["explanation"]),
            ]
        )
    lines.extend(
        ["", "IMPROVED SPECIFICATION", "", _safe_display_text(payload["improved_spec"])]
    )
    return "\n".join(lines)


def _render_ai_review_markdown(payload: dict[str, Any]) -> str:
    report = payload["deterministic"]
    draft_report = payload["draft_deterministic"]
    contradictions = payload["contradictions"]
    lines = [
        "# SpecForge Gate AI Review",
        "",
        f"- Provider: `{_safe_display_text(payload['provider'])}`",
        f"- Model: `{_safe_display_text(payload['model'])}`",
        "",
        "## Deterministic report",
        "",
        f"Status: **{_safe_display_text(report['status'])}**",
        "",
        "## Draft deterministic report",
        "",
        f"Status: **{_safe_display_text(draft_report['status'])}**",
        "",
        (
            "Findings: "
            f"{draft_report['summary']['errors']} errors, "
            f"{draft_report['summary']['warnings']} warnings, "
            f"{draft_report['summary']['info']} info"
        ),
        "",
        "## Contradictions",
        "",
    ]
    if not contradictions:
        lines.append("No direct contradictions reported.")
    else:
        for index, item in enumerate(contradictions, start=1):
            lines.extend(
                [
                    f"### Contradiction {index}",
                    "",
                    f"- Statement A: {_safe_display_text(item['statement_a'])}",
                    f"- Statement B: {_safe_display_text(item['statement_b'])}",
                    f"- Explanation: {_safe_display_text(item['explanation'])}",
                    "",
                ]
            )

    lines.extend(
        ["## Improved specification", "", _safe_display_text(payload["improved_spec"])]
    )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "ai-review":
        return _run_ai_review(args)
    if args.command != "check":
        return 2

    try:
        config = load_project_config(args.config)
    except ConfigError as exc:
        print(f"specgate: {exc}", file=sys.stderr)
        return 2

    force_multi = len(args.paths) > 1 or any(path.is_dir() for path in args.paths)
    reports: list[AnalysisReport] = []
    for path, discovered in _expand_paths(args.paths):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"specgate: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        if discovered and config.excludes(path):
            continue
        try:
            reports.append(analyze_text(text, source=str(path), config=config))
        except SuppressionError as exc:
            print(f"specgate: {path}:{exc.line}: {exc}", file=sys.stderr)
            return 2

    _print_stdout(_render_output(args.format, reports, force_multi=force_multi))
    errors = sum(report.count(Severity.ERROR) for report in reports)
    warnings = sum(report.count(Severity.WARNING) for report in reports)
    return int(_should_fail(args.fail_on, errors, warnings))


if __name__ == "__main__":
    raise SystemExit(main())
