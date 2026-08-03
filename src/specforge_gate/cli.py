"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from specforge_gate.engine import analyze_text
from specforge_gate.models import Severity
from specforge_gate.reporters import render_json, render_markdown, render_text

_RENDERERS = {"text": render_text, "json": render_json, "markdown": render_markdown}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specgate", description="Lint software requirements.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Analyze a Markdown or text file.")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=tuple(_RENDERERS), default="text")
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "check":
        return 2

    try:
        text = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"specgate: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    report = analyze_text(text, source=str(args.path))
    print(_RENDERERS[args.format](report))
    return int(
        _should_fail(
            args.fail_on,
            report.count(Severity.ERROR),
            report.count(Severity.WARNING),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
