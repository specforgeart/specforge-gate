from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml

from specforge_gate.cli import main
from specforge_gate.engine import analyze_text

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = REPOSITORY_ROOT / "examples" / "corpus"
MANIFEST_PATH = CORPUS_ROOT / "manifest.yml"
FIXTURE_SUFFIXES = {".md", ".markdown", ".txt"}
RULE_IDS = {"SG001", "SG002", "SG003", "SG004", "SG005", "SG101", "SG102", "SG103"}


def _load_manifest() -> dict[str, Any]:
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


MANIFEST = _load_manifest()
CASES = tuple(MANIFEST["cases"])
CASE_BY_ID = {case["id"]: case for case in CASES}


def _fixture_path(case: dict[str, Any]) -> Path:
    return CORPUS_ROOT / case["path"]


def _expected_finding_counts(case: dict[str, Any]) -> Counter[tuple[str, str]]:
    return Counter(
        (finding["rule_id"], finding["severity"])
        for finding in case["expected"]["findings"]
    )


def _actual_finding_counts(case: dict[str, Any]) -> Counter[tuple[str, str]]:
    path = _fixture_path(case)
    report = analyze_text(path.read_text(encoding="utf-8"), source=str(path))
    return Counter((finding.rule_id, finding.severity.value) for finding in report.findings)


def test_manifest_and_fixture_inventory_are_exact() -> None:
    assert MANIFEST["version"] == 1
    assert len(CASES) == 40

    ids = [case["id"] for case in CASES]
    paths = [case["path"] for case in CASES]
    assert len(ids) == len(set(ids))
    assert len(paths) == len(set(paths))

    fixture_files = {
        path.relative_to(CORPUS_ROOT).as_posix()
        for path in CORPUS_ROOT.rglob("*")
        if path.is_file() and path.suffix in FIXTURE_SUFFIXES
    }
    assert fixture_files == set(paths)
    assert "manifest.yml" not in fixture_files

    corpus_root = CORPUS_ROOT.resolve()
    for case in CASES:
        path = _fixture_path(case)
        assert path.resolve().is_relative_to(corpus_root)
        assert path.is_file()
        assert path.read_text(encoding="utf-8").strip()

    assert (REPOSITORY_ROOT / "examples" / "bad" / "export-task.md").is_file()
    assert (REPOSITORY_ROOT / "examples" / "improved" / "export-task.md").is_file()


def test_manifest_composition_matches_issue_contract() -> None:
    assert Counter(case["category"] for case in CASES) == {
        "bad": 16,
        "improved": 16,
        "boundary": 8,
    }
    assert Counter(case["language"] for case in CASES) == {"en": 24, "ru": 16}
    assert all(case["category"] in {"bad", "improved", "boundary"} for case in CASES)
    assert all(case["language"] in {"en", "ru"} for case in CASES)
    assert all(case["domain"] for case in CASES)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_corpus_case_matches_expected_findings(case: dict[str, Any]) -> None:
    path = _fixture_path(case)
    report = analyze_text(path.read_text(encoding="utf-8"), source=str(path))

    assert report.status.value == case["expected"]["status"]
    assert Counter(
        (finding.rule_id, finding.severity.value) for finding in report.findings
    ) == _expected_finding_counts(case)

    expected_locations = Counter(
        (finding["rule_id"], finding["severity"], finding["line"])
        for finding in case["expected"]["findings"]
        if "line" in finding
    )
    actual_locations = Counter(
        (finding.rule_id, finding.severity.value, finding.line)
        for finding in report.findings
    )
    for location, expected_count in expected_locations.items():
        assert actual_locations[location] == expected_count


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_corpus_case_cli_exit_codes(
    case: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    path = _fixture_path(case)
    expected = case["expected"]["exit_codes"]
    commands = (
        ([], expected["default"]),
        (["--fail-on", "none"], expected["fail_on_none"]),
        (["--fail-on", "warning"], expected["fail_on_warning"]),
    )

    for extra_args, expected_code in commands:
        assert main(["check", str(path), *extra_args]) == expected_code
        capsys.readouterr()


def test_manifest_declares_positive_and_negative_coverage_for_every_rule() -> None:
    coverage = MANIFEST["rule_coverage"]
    assert set(coverage) == RULE_IDS

    for rule_id, case_ids in coverage.items():
        positive = CASE_BY_ID[case_ids["positive"]]
        negative = CASE_BY_ID[case_ids["negative"]]
        assert any(
            finding["rule_id"] == rule_id
            for finding in positive["expected"]["findings"]
        )
        assert all(
            finding["rule_id"] != rule_id
            for finding in negative["expected"]["findings"]
        )
        assert _actual_finding_counts(positive)[(rule_id, _rule_severity(rule_id))] > 0
        assert not any(
            found_rule == rule_id for found_rule, _severity in _actual_finding_counts(negative)
        )


def _rule_severity(rule_id: str) -> str:
    if rule_id in {"SG001", "SG002", "SG003", "SG102"}:
        return "error"
    if rule_id in {"SG004", "SG005", "SG101"}:
        return "warning"
    return "info"


def test_single_file_json_contract(capsys: pytest.CaptureFixture[str]) -> None:
    case = CASE_BY_ID["bad-en-010-file-upload-vague"]
    path = _fixture_path(case)

    assert main(["check", str(path), "--format", "json", "--fail-on", "none"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == {"source", "status", "summary", "findings"}
    assert payload["source"] == str(path)
    assert payload["status"] == "NEEDS WORK"
    assert payload["summary"] == {"errors": 1, "warnings": 3, "info": 0, "total": 4}
    assert all(
        set(finding) == {"rule_id", "severity", "message", "suggestion", "line", "excerpt"}
        for finding in payload["findings"]
    )
    assert [finding["rule_id"] for finding in payload["findings"]] == [
        "SG101",
        "SG101",
        "SG101",
        "SG102",
    ]
    ordering = [
        (finding["line"] is None, finding["line"] or 0, finding["rule_id"])
        for finding in payload["findings"]
    ]
    assert ordering == sorted(ordering)


def test_single_file_markdown_contract(capsys: pytest.CaptureFixture[str]) -> None:
    case = CASE_BY_ID["bad-en-002-password-reset-vague"]
    path = _fixture_path(case)

    assert main(["check", str(path), "--format", "markdown", "--fail-on", "none"]) == 0
    output = capsys.readouterr().out

    assert output.startswith("# SpecForge Gate: NEEDS WORK\n")
    assert "| Error | 1 |" in output
    assert "| Warning | 1 |" in output
    assert "| Info | 0 |" in output
    headings = re.findall(r"^### `([A-Z0-9]+)` · ([a-z]+)(?: \(line (\d+)\))?$", output, re.M)
    assert headings == [("SG101", "warning", "13"), ("SG102", "error", "13")]


def test_directory_json_contract_discovers_all_forty_fixtures(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(REPOSITORY_ROOT)
    relative_root = Path("examples/corpus")

    assert main(["check", str(relative_root), "--format", "json", "--fail-on", "none"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == {"status", "summary", "reports"}
    assert payload["status"] == "NEEDS WORK"
    assert payload["summary"]["files"] == 40
    assert len(payload["reports"]) == 40

    sources = [report["source"].replace("\\", "/") for report in payload["reports"]]
    assert sources == sorted(sources)
    assert "examples/corpus/boundary/en/036-directory-text-input.txt" in sources
    assert all(not source.endswith("manifest.yml") for source in sources)

    expected_counts = Counter()
    for case in CASES:
        expected_counts.update(
            finding["severity"] for finding in case["expected"]["findings"]
        )
    assert payload["summary"] == {
        "files": 40,
        "errors": expected_counts["error"],
        "warnings": expected_counts["warning"],
        "info": expected_counts["info"],
        "total": sum(expected_counts.values()),
    }
