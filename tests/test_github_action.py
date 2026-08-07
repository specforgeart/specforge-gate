from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from specforge_gate.github_action import (
    ActionOptions,
    _changed_markdown_files,
    _limit_summary,
    execute,
    main,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

_PASSING_SPEC = """# Example

## Goal
Provide a deterministic result.

## Expected result
A report contains the selected record.

## Out of scope
- External delivery.

## Acceptance criteria
- Given 1 record, when the report runs, then it contains 1 row.

## Errors and edge cases
- Missing data returns an empty report.
"""

_WARNING_ONLY_SPEC = """# Example

## Goal
Provide a deterministic result.

## Expected result
A report contains the selected record.

## Acceptance criteria
- Given 1 record, when the report runs, then it contains 1 row.

## Errors and edge cases
- Missing data returns an empty report.
"""


def _options(
    workspace: Path,
    *,
    raw_paths: str,
    fail_on: str = "error",
    config: str = "",
    event_name: str = "workflow_dispatch",
    base_sha: str = "",
    head_sha: str = "",
    summary_path: Path | None = None,
    output_path: Path | None = None,
) -> ActionOptions:
    return ActionOptions(
        workspace=workspace,
        raw_paths=raw_paths,
        fail_on=fail_on,
        config=config,
        event_name=event_name,
        base_sha=base_sha,
        head_sha=head_sha,
        summary_path=summary_path,
        output_path=output_path,
    )


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def test_explicit_paths_write_pass_summary_and_outputs(tmp_path: Path) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_PASSING_SPEC, encoding="utf-8")
    summary_path = tmp_path / "summary.md"
    output_path = tmp_path / "outputs.txt"

    assert (
        main(
            [
                "--workspace",
                str(tmp_path),
                "--paths",
                "task.md",
                "--summary-path",
                str(summary_path),
                "--output-path",
                str(output_path),
            ]
        )
        == 0
    )

    summary = summary_path.read_text(encoding="utf-8")
    assert summary.startswith("# SpecForge Gate: PASS\n")
    assert "| Files checked | 1 |" in summary
    assert "- `task.md`" in summary
    assert "No findings." in summary

    outputs = output_path.read_text(encoding="utf-8")
    assert "status=PASS\n" in outputs
    assert "files=1\n" in outputs
    assert "total=0\n" in outputs



def test_job_summary_lists_findings_and_locations(tmp_path: Path) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_WARNING_ONLY_SPEC, encoding="utf-8")
    summary_path = tmp_path / "summary.md"

    exit_code = main(
        [
            "--workspace",
            str(tmp_path),
            "--paths",
            "task.md",
            "--fail-on",
            "none",
            "--summary-path",
            str(summary_path),
        ]
    )

    summary = summary_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert summary.startswith("# SpecForge Gate: NEEDS WORK\n")
    assert "### `SG004` · warning" in summary
    assert "**Location:** `task.md`" in summary
    assert "**Suggested fix:**" in summary

@pytest.mark.parametrize(
    ("fail_on", "expected_code"),
    [("none", 0), ("warning", 1), ("error", 0)],
)
def test_warning_only_result_follows_fail_threshold(
    tmp_path: Path, fail_on: str, expected_code: int
) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_WARNING_ONLY_SPEC, encoding="utf-8")

    result = execute(_options(tmp_path, raw_paths="task.md", fail_on=fail_on))

    assert result.status == "NEEDS WORK"
    assert result.errors == 0
    assert result.warnings == 1
    assert result.exit_code == expected_code


def test_explicit_directory_honors_exclusions_and_rule_configuration(tmp_path: Path) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "pass.md").write_text(_PASSING_SPEC, encoding="utf-8")
    (specs / "skip.md").write_text("Make it fast.", encoding="utf-8")
    (tmp_path / ".specgate.yml").write_text(
        """version: 1
rules:
  SG004:
    enabled: false
  SG101:
    severity: error
exclude:
  - specs/skip.md
""",
        encoding="utf-8",
    )

    result = execute(_options(tmp_path, raw_paths="specs"))

    assert result.status == "PASS"
    assert result.files == ("specs/pass.md",)
    assert result.total == 0



def test_rule_disable_and_severity_override_are_honored(tmp_path: Path) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_WARNING_ONLY_SPEC, encoding="utf-8")
    (tmp_path / "strict.yml").write_text(
        """version: 1
rules:
  SG004:
    severity: error
""",
        encoding="utf-8",
    )
    (tmp_path / "disabled.yml").write_text(
        """version: 1
rules:
  SG004:
    enabled: false
""",
        encoding="utf-8",
    )

    strict = execute(
        _options(tmp_path, raw_paths="task.md", config="strict.yml", fail_on="error")
    )
    disabled = execute(
        _options(tmp_path, raw_paths="task.md", config="disabled.yml", fail_on="error")
    )

    assert strict.errors == 1
    assert strict.warnings == 0
    assert strict.exit_code == 1
    assert disabled.status == "PASS"
    assert disabled.total == 0


def test_main_writes_error_summary_and_outputs_for_invalid_config(tmp_path: Path) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "invalid.yml").write_text("version: 2\n", encoding="utf-8")
    summary_path = tmp_path / "summary.md"
    output_path = tmp_path / "outputs.txt"

    exit_code = main(
        [
            "--workspace",
            str(tmp_path),
            "--paths",
            "task.md",
            "--config",
            "invalid.yml",
            "--summary-path",
            str(summary_path),
            "--output-path",
            str(output_path),
        ]
    )

    assert exit_code == 2
    assert summary_path.read_text(encoding="utf-8").startswith(
        "# SpecForge Gate: ERROR\n"
    )
    assert "config.version: expected 1" in summary_path.read_text(encoding="utf-8")
    assert "status=ERROR\n" in output_path.read_text(encoding="utf-8")

def test_explicit_glob_with_no_matches_is_a_successful_empty_report(tmp_path: Path) -> None:
    result = execute(_options(tmp_path, raw_paths="requirements/**/*.md"))

    assert result.status == "PASS"
    assert result.files == ()
    assert result.exit_code == 0


def test_invalid_configuration_is_actionable_without_traceback(tmp_path: Path) -> None:
    specification = tmp_path / "task.md"
    specification.write_text(_PASSING_SPEC, encoding="utf-8")
    config = tmp_path / "invalid.yml"
    config.write_text("version: 2\n", encoding="utf-8")

    result = execute(
        _options(tmp_path, raw_paths="task.md", config="invalid.yml")
    )

    assert result.status == "ERROR"
    assert result.exit_code == 2
    assert result.error == "config.version: expected 1"


def test_paths_outside_workspace_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.md"
    outside.write_text(_PASSING_SPEC, encoding="utf-8")

    result = execute(_options(tmp_path, raw_paths="../outside.md"))

    assert result.exit_code == 2
    assert result.error == "path escapes the workspace: ../outside.md"


def test_pull_request_selection_includes_added_modified_and_renamed_markdown(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "config", "user.email", "specforge@example.test")
    _git(tmp_path, "config", "user.name", "SpecForge Test")

    (tmp_path / "modified.md").write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "renamed.md").write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "deleted.md").write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "ignored.txt").write_text(_PASSING_SPEC, encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "--quiet", "-m", "base")
    base_sha = _git(tmp_path, "rev-parse", "HEAD")

    (tmp_path / "modified.md").write_text(_PASSING_SPEC + "\n", encoding="utf-8")
    _git(tmp_path, "mv", "renamed.md", "renamed.markdown")
    (tmp_path / "added.md").write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "added.txt").write_text(_PASSING_SPEC, encoding="utf-8")
    (tmp_path / "deleted.md").unlink()
    _git(tmp_path, "add", "--all")
    _git(tmp_path, "commit", "--quiet", "-m", "head")
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    selected = _changed_markdown_files(tmp_path.resolve(), base_sha, head_sha)

    assert tuple(path.name for path in selected) == (
        "added.md",
        "modified.md",
        "renamed.markdown",
    )


def test_pull_request_mode_requires_full_history(tmp_path: Path) -> None:
    _git(tmp_path, "init", "--quiet")

    result = execute(
        _options(
            tmp_path,
            raw_paths="",
            event_name="pull_request",
            base_sha="0" * 40,
            head_sha="1" * 40,
        )
    )

    assert result.exit_code == 2
    assert result.error is not None
    assert "fetch-depth: 0" in result.error


def test_non_pull_request_requires_explicit_paths(tmp_path: Path) -> None:
    result = execute(_options(tmp_path, raw_paths=""))

    assert result.exit_code == 2
    assert result.error == "paths input is required outside a pull_request event"



def test_oversized_job_summary_is_truncated_safely() -> None:
    summary = "# Summary\n" + ("данные\n" * 200_000)

    limited = _limit_summary(summary)

    assert len(limited.encode("utf-8")) <= 900_000
    assert "Summary truncated" in limited

def test_action_metadata_exposes_read_only_composite_contract() -> None:
    metadata = yaml.safe_load((REPOSITORY_ROOT / "action.yml").read_text(encoding="utf-8"))

    assert metadata["runs"]["using"] == "composite"
    assert set(metadata["inputs"]) == {"paths", "fail-on", "config", "python-version"}
    assert set(metadata["outputs"]) == {
        "status",
        "files",
        "errors",
        "warnings",
        "info",
        "total",
    }
    steps = metadata["runs"]["steps"]
    assert steps[0]["uses"] == "actions/setup-python@v7"
    assert steps[-1]["shell"] == "bash"

    raw = (REPOSITORY_ROOT / "action.yml").read_text(encoding="utf-8")
    assert "github.token" not in raw
    assert "GITHUB_TOKEN" not in raw


def test_smoke_and_consumer_workflows_use_read_only_permissions() -> None:
    smoke = yaml.load(
        (REPOSITORY_ROOT / ".github/workflows/action-smoke.yml").read_text(
            encoding="utf-8"
        ),
        Loader=yaml.BaseLoader,
    )
    consumer = yaml.load(
        (REPOSITORY_ROOT / ".github/examples/specforge-gate.yml").read_text(
            encoding="utf-8"
        ),
        Loader=yaml.BaseLoader,
    )

    assert smoke["permissions"] == {"contents": "read"}
    assert consumer["permissions"] == {"contents": "read"}
    checkout = consumer["jobs"]["requirements"]["steps"][0]
    assert checkout["with"]["fetch-depth"] == "0"
    action_step: dict[str, Any] = consumer["jobs"]["requirements"]["steps"][1]
    assert action_step["uses"] == "specforgeart/specforge-gate@main"
