"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    return parser


def _should_fail(fail_on: str, errors: int, warnings: int) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "warning":
        return errors + warnings > 0
    return errors > 0


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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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

    print(_render_output(args.format, reports, force_multi=force_multi))
    errors = sum(report.count(Severity.ERROR) for report in reports)
    warnings = sum(report.count(Severity.WARNING) for report in reports)
    return int(_should_fail(args.fail_on, errors, warnings))


if __name__ == "__main__":
    raise SystemExit(main())
