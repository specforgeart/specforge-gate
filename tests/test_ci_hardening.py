from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = "34e114876b0b11c390a56381ad16ebd13914f8d5"
SETUP_PYTHON_SHA = "5fda3b95a4ea91299a34e894583c3862153e4b97"
DEPENDENCY_REVIEW_SHA = "a1d282b36b6f3519aa1f3fc636f609c47dddb294"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _yaml(path: str) -> dict[str, Any]:
    return yaml.load((ROOT / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _third_party_uses(path: Path) -> list[str]:
    uses: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.search(r"\buses:\s*([^#\s]+)", line)
        if not match:
            continue
        value = match.group(1)
        if value.startswith("./"):
            continue
        uses.append(value)
    return uses


def test_linux_ci_runs_canonical_quality_and_python_matrix() -> None:
    workflow = _yaml(".github/workflows/ci.yml")
    jobs = workflow["jobs"]

    assert set(jobs) == {"static-package", "tests", "ci-gate"}
    assert jobs["tests"]["strategy"]["matrix"]["python-version"] == ["3.11", "3.12", "3.13"]
    assert jobs["ci-gate"]["needs"] == ["static-package", "tests"]

    static_steps = jobs["static-package"]["steps"]
    canonical = next(step for step in static_steps if step.get("name") == "Canonical Linux quality")
    assert canonical["env"] == {"SKIP_HOOKS": "1", "PYTHON": "python"}
    assert canonical["run"].splitlines() == [
        "bash scripts/bootstrap.sh",
        "bash scripts/check.sh",
    ]

    test_runs = "\n".join(step.get("run", "") for step in jobs["tests"]["steps"])
    assert "pytest" in test_runs
    assert "--cov-branch" in test_runs
    assert "--cov-fail-under=85" in test_runs
    assert "python -m build" not in test_runs


def test_action_smoke_exposes_one_stable_job_and_three_scenarios() -> None:
    workflow = _yaml(".github/workflows/action-smoke.yml")
    jobs = workflow["jobs"]
    assert set(jobs) == {"action-smoke"}

    steps = jobs["action-smoke"]["steps"]
    names = {step.get("name", "") for step in steps}
    assert "Run local action on a passing specification" in names
    assert "Run local action in report-only mode" in names
    assert "Run local action on changed Markdown files" in names


def test_dependency_review_blocks_moderate_or_higher() -> None:
    workflow = _yaml(".github/workflows/dependency-review.yml")
    steps = workflow["jobs"]["dependency-review"]["steps"]
    review = next(step for step in steps if "dependency-review-action" in step.get("uses", ""))
    assert review["with"]["fail-on-severity"] == "moderate"


def test_scheduled_dependency_audit_uses_pinned_tool() -> None:
    workflow = _yaml(".github/workflows/dependency-audit.yml")
    triggers = workflow["on"]
    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    runs = "\n".join(
        step.get("run", "")
        for step in workflow["jobs"]["dependency-audit"]["steps"]
    )
    assert 'pip-audit==2.10.1' in runs
    assert "python -m pip_audit ." in runs


def test_canonical_scripts_enable_branch_coverage() -> None:
    for relative in ("scripts/check.sh", "scripts/check.ps1"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "--cov-branch" in text
        assert "--cov-fail-under=85" in text


def test_third_party_actions_are_full_sha_pinned() -> None:
    files = [
        ROOT / "action.yml",
        *sorted((ROOT / ".github/workflows").glob("*.yml")),
        ROOT / ".github/examples/specforge-gate.yml",
    ]
    found: list[str] = []
    for path in files:
        for use in _third_party_uses(path):
            owner_action, ref = use.rsplit("@", 1)
            if owner_action == "specforgeart/specforge-gate":
                continue
            assert SHA_RE.fullmatch(ref), f"{path} uses movable ref {use}"
            found.append(use)

    assert f"actions/checkout@{CHECKOUT_SHA}" in found
    assert f"actions/setup-python@{SETUP_PYTHON_SHA}" in found
    assert f"actions/dependency-review-action@{DEPENDENCY_REVIEW_SHA}" in found


def test_pull_request_validation_workflows_are_read_only() -> None:
    for relative in (
        ".github/workflows/ci.yml",
        ".github/workflows/windows-quality.yml",
        ".github/workflows/action-smoke.yml",
        ".github/workflows/dependency-review.yml",
        ".github/workflows/pr-policy.yml",
    ):
        workflow = _yaml(relative)
        assert workflow["permissions"] == {"contents": "read"}


def test_quality_gate_documentation_names_stable_protection_contexts() -> None:
    text = (ROOT / "docs/quality-gates.md").read_text(encoding="utf-8")
    for context in (
        "`ci-gate`",
        "`windows-quality`",
        "`action-smoke`",
        "`pr-policy`",
        "`dependency-review`",
        "`CodeQL`",
    ):
        assert context in text


def test_documented_consumer_checkout_is_sha_pinned() -> None:
    for relative in ("README.md", "docs/github-action.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert f"actions/checkout@{CHECKOUT_SHA} # v4.3.1" in text
        assert "actions/checkout@v4" not in text
