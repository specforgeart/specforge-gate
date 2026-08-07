"""GitHub Action adapter for SpecForge Gate."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from specforge_gate.config import ConfigError, ProjectConfig, load_project_config
from specforge_gate.engine import analyze_text
from specforge_gate.models import AnalysisReport, Severity, Status
from specforge_gate.suppression import SuppressionError

_PR_SUFFIXES = {".md", ".markdown"}
_EXPLICIT_SUFFIXES = _PR_SUFFIXES | {".txt"}
_FAIL_LEVELS = {"none", "warning", "error"}
_SUMMARY_BYTE_LIMIT = 900_000


class ActionError(ValueError):
    """Raised when the action cannot select or analyze its inputs."""


@dataclass(frozen=True, slots=True)
class ActionOptions:
    workspace: Path
    raw_paths: str
    fail_on: str
    config: str
    event_name: str
    base_sha: str
    head_sha: str
    summary_path: Path | None
    output_path: Path | None


@dataclass(frozen=True, slots=True)
class ActionResult:
    status: str
    files: tuple[str, ...]
    reports: tuple[AnalysisReport, ...]
    errors: int
    warnings: int
    info: int
    exit_code: int
    error: str | None = None

    @property
    def total(self) -> int:
        return self.errors + self.warnings + self.info


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specgate-action",
        description="Run SpecForge Gate as a GitHub composite action.",
    )
    parser.add_argument("--workspace", type=Path, default=Path(os.getenv("GITHUB_WORKSPACE", ".")))
    parser.add_argument("--paths", default=os.getenv("INPUT_PATHS", ""))
    parser.add_argument("--fail-on", default=os.getenv("INPUT_FAIL_ON", "error"))
    parser.add_argument("--config", default=os.getenv("INPUT_CONFIG", ""))
    parser.add_argument("--event-name", default=os.getenv("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--base-sha", default=os.getenv("SPECFORGE_BASE_SHA", ""))
    parser.add_argument("--head-sha", default=os.getenv("SPECFORGE_HEAD_SHA", ""))
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=_optional_path(os.getenv("GITHUB_STEP_SUMMARY", "")),
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=_optional_path(os.getenv("GITHUB_OUTPUT", "")),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = ActionOptions(
        workspace=args.workspace,
        raw_paths=args.paths,
        fail_on=args.fail_on,
        config=args.config,
        event_name=args.event_name,
        base_sha=args.base_sha,
        head_sha=args.head_sha,
        summary_path=args.summary_path,
        output_path=args.output_path,
    )
    result = execute(options)
    _write_summary(options.summary_path, result)
    _write_outputs(options.output_path, result)
    if result.error:
        print(f"specgate-action: {result.error}", file=sys.stderr)
    else:
        print(
            f"SpecForge Gate: {result.status}; files={len(result.files)}; "
            f"errors={result.errors}; warnings={result.warnings}; info={result.info}"
        )
    return result.exit_code


def execute(options: ActionOptions) -> ActionResult:
    workspace = options.workspace.resolve()
    try:
        if options.fail_on not in _FAIL_LEVELS:
            raise ActionError("fail-on must be one of: none, warning, error")
        if not workspace.is_dir():
            raise ActionError(f"workspace does not exist or is not a directory: {workspace}")

        config = _load_action_config(workspace, options.config)
        selected = _select_input_files(options, workspace)
        selected = tuple(path for path in selected if not config.excludes(path))
        reports = _analyze_files(workspace, selected, config)
    except (ActionError, ConfigError) as exc:
        return _error_result(str(exc))

    errors = sum(report.count(Severity.ERROR) for report in reports)
    warnings = sum(report.count(Severity.WARNING) for report in reports)
    info = sum(report.count(Severity.INFO) for report in reports)
    status = (
        Status.PASS.value if errors + warnings + info == 0 else Status.NEEDS_WORK.value
    )
    relative_files = tuple(_relative_source(workspace, path) for path in selected)
    exit_code = int(_should_fail(options.fail_on, errors, warnings))
    return ActionResult(
        status=status,
        files=relative_files,
        reports=reports,
        errors=errors,
        warnings=warnings,
        info=info,
        exit_code=exit_code,
    )


def _load_action_config(workspace: Path, raw_config: str) -> ProjectConfig:
    if not raw_config.strip():
        return load_project_config(start=workspace)
    config_path = _resolve_workspace_path(workspace, raw_config.strip())
    return load_project_config(config_path)


def _select_input_files(options: ActionOptions, workspace: Path) -> tuple[Path, ...]:
    if options.raw_paths.strip():
        return _expand_explicit_paths(workspace, options.raw_paths)
    if options.event_name != "pull_request":
        raise ActionError("paths input is required outside a pull_request event")
    if not options.base_sha or not options.head_sha:
        raise ActionError("pull_request base and head SHAs are unavailable")
    return _changed_markdown_files(workspace, options.base_sha, options.head_sha)


def _expand_explicit_paths(workspace: Path, raw_paths: str) -> tuple[Path, ...]:
    selected: set[Path] = set()
    for raw_value in raw_paths.splitlines():
        value = raw_value.strip()
        if not value:
            continue
        if any(character in value for character in "*?["):
            if Path(value).is_absolute():
                raise ActionError(f"glob path must be relative to the workspace: {value}")
            try:
                matches = tuple(workspace.glob(value))
            except (NotImplementedError, ValueError) as exc:
                raise ActionError(f"invalid glob path: {value}") from exc
            for match in matches:
                selected.update(_expand_explicit_match(workspace, match, value))
            continue
        match = _resolve_workspace_path(workspace, value)
        if not match.exists():
            raise ActionError(f"explicit path does not exist: {value}")
        selected.update(_expand_explicit_match(workspace, match, value))
    return tuple(sorted(selected, key=lambda path: _relative_source(workspace, path)))


def _expand_explicit_match(workspace: Path, path: Path, source_value: str) -> set[Path]:
    resolved = path.resolve()
    _require_within_workspace(workspace, resolved, source_value)
    if resolved.is_dir():
        selected: set[Path] = set()
        for candidate in resolved.rglob("*"):
            if not candidate.is_file() or candidate.suffix not in _EXPLICIT_SUFFIXES:
                continue
            candidate_resolved = candidate.resolve()
            _require_within_workspace(workspace, candidate_resolved, str(candidate))
            selected.add(candidate_resolved)
        return selected
    if not resolved.is_file():
        raise ActionError(f"explicit path is not a regular file: {source_value}")
    if resolved.suffix not in _EXPLICIT_SUFFIXES:
        raise ActionError(
            f"unsupported explicit file type for {source_value}; expected .md, .markdown, or .txt"
        )
    return {resolved}


def _changed_markdown_files(workspace: Path, base_sha: str, head_sha: str) -> tuple[Path, ...]:
    _require_commit(workspace, base_sha, "base")
    _require_commit(workspace, head_sha, "head")
    command = [
        "git",
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        "--diff-filter=AMR",
        f"{base_sha}...{head_sha}",
        "--",
    ]
    try:
        completed = subprocess.run(command, cwd=workspace, capture_output=True, check=False)
    except OSError as exc:
        raise ActionError(f"cannot execute git diff: {exc}") from exc
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ActionError(f"cannot calculate pull-request changes: {stderr or 'git diff failed'}")

    selected: set[Path] = set()
    tokens = completed.stdout.split(b"\0")
    index = 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index].decode("utf-8", errors="surrogateescape")
        index += 1
        if status.startswith("R"):
            if index + 1 >= len(tokens):
                raise ActionError("cannot parse renamed path from git diff output")
            index += 1  # Old path is intentionally ignored.
            raw_path = tokens[index]
            index += 1
        else:
            if index >= len(tokens):
                raise ActionError("cannot parse path from git diff output")
            raw_path = tokens[index]
            index += 1
        relative = raw_path.decode("utf-8", errors="surrogateescape")
        candidate = _resolve_workspace_path(workspace, relative)
        if candidate.suffix in _PR_SUFFIXES and candidate.is_file():
            selected.add(candidate.resolve())
    return tuple(sorted(selected, key=lambda path: _relative_source(workspace, path)))


def _require_commit(workspace: Path, sha: str, label: str) -> None:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ActionError(f"cannot execute git: {exc}") from exc
    if completed.returncode != 0:
        raise ActionError(
            f"pull-request {label} commit {sha} is unavailable; "
            "use actions/checkout with fetch-depth: 0"
        )


def _analyze_files(
    workspace: Path, paths: Iterable[Path], config: ProjectConfig
) -> tuple[AnalysisReport, ...]:
    reports: list[AnalysisReport] = []
    for path in paths:
        source = _relative_source(workspace, path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ActionError(f"cannot read {source}: {exc}") from exc
        try:
            reports.append(analyze_text(text, source=source, config=config))
        except SuppressionError as exc:
            raise ActionError(f"{source}:{exc.line}: {exc}") from exc
    return tuple(reports)


def _write_summary(path: Path | None, result: ActionResult) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_limit_summary(_render_summary(result)), encoding="utf-8")


def _render_summary(result: ActionResult) -> str:
    heading = "ERROR" if result.error else result.status
    lines = [
        f"# SpecForge Gate: {heading}",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Files checked | {len(result.files)} |",
        f"| Errors | {result.errors} |",
        f"| Warnings | {result.warnings} |",
        f"| Info | {result.info} |",
        f"| Total findings | {result.total} |",
    ]
    if result.error:
        lines.extend(["", "## Action error", "", _escape_markdown(result.error)])
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["", "## Checked files", ""])
    if result.files:
        lines.extend(f"- `{_escape_code(file_path)}`" for file_path in result.files)
    else:
        lines.append("No matching files were selected.")

    findings = [
        (report.source, finding)
        for report in result.reports
        for finding in report.findings
    ]
    lines.extend(["", "## Findings", ""])
    if not findings:
        lines.append("No findings.")
    else:
        for source, finding in findings:
            location = f":{finding.line}" if finding.line else ""
            lines.extend(
                [
                    f"### `{finding.rule_id}` · {finding.severity.value}",
                    "",
                    f"**Location:** `{_escape_code(source)}{location}`",
                    "",
                    _escape_markdown(finding.message),
                    "",
                    f"**Suggested fix:** {_escape_markdown(finding.suggestion)}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"



def _limit_summary(summary: str) -> str:
    encoded = summary.encode("utf-8")
    if len(encoded) <= _SUMMARY_BYTE_LIMIT:
        return summary
    suffix = (
        "\n\n> Summary truncated before GitHub's per-step size limit. "
        "Counts and action outputs remain complete.\n"
    )
    available = _SUMMARY_BYTE_LIMIT - len(suffix.encode("utf-8"))
    prefix = encoded[:available].decode("utf-8", errors="ignore").rstrip()
    return prefix + suffix

def _write_outputs(path: Path | None, result: ActionResult) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {
        "status": "ERROR" if result.error else result.status,
        "files": len(result.files),
        "errors": result.errors,
        "warnings": result.warnings,
        "info": result.info,
        "total": result.total,
    }
    with path.open("a", encoding="utf-8", newline="\n") as output:
        for name, value in values.items():
            output.write(f"{name}={value}\n")


def _error_result(message: str) -> ActionResult:
    return ActionResult(
        status="ERROR",
        files=(),
        reports=(),
        errors=0,
        warnings=0,
        info=0,
        exit_code=2,
        error=message,
    )


def _should_fail(fail_on: str, errors: int, warnings: int) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "warning":
        return errors + warnings > 0
    return errors > 0


def _resolve_workspace_path(workspace: Path, value: str) -> Path:
    path = Path(value)
    candidate = path if path.is_absolute() else workspace / path
    resolved = candidate.resolve()
    _require_within_workspace(workspace, resolved, value)
    return resolved


def _require_within_workspace(workspace: Path, path: Path, source_value: str) -> None:
    try:
        path.relative_to(workspace)
    except ValueError as exc:
        raise ActionError(f"path escapes the workspace: {source_value}") from exc


def _relative_source(workspace: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace).as_posix()


def _escape_code(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ").replace("`", "\\`")


def _escape_markdown(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ")


def _optional_path(value: str) -> Path | None:
    return Path(value) if value else None


if __name__ == "__main__":
    raise SystemExit(main())
