from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mutation_summary.py"


def _write_meta(root: Path, values: dict[str, int | None]) -> None:
    path = root / "specforge_gate" / "engine.py.meta"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"exit_code_by_key": values}), encoding="utf-8")


def test_mutation_summary_classifies_mutmut_exit_codes(tmp_path: Path) -> None:
    mutants = tmp_path / "mutants"
    _write_meta(
        mutants,
        {
            "killed": 1,
            "survived": 0,
            "no-tests": 5,
            "timeout": 36,
            "suspicious": 35,
            "skipped": 34,
        },
    )
    output = tmp_path / "summary.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mutants",
            str(mutants),
            "--output",
            str(output),
            "--require-complete",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["total_mutants"] == 6
    assert summary["killed"] == 1
    assert summary["survived"] == 1
    assert summary["no_tests"] == 1
    assert summary["timeout"] == 1
    assert summary["suspicious"] == 1
    assert summary["skipped"] == 1
    assert summary["kill_rate_percent"] == 50.0


def test_mutation_summary_rejects_incomplete_run(tmp_path: Path) -> None:
    mutants = tmp_path / "mutants"
    _write_meta(mutants, {"pending": None})

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mutants",
            str(mutants),
            "--output",
            str(tmp_path / "summary.json"),
            "--require-complete",
        ],
        check=False,
    )

    assert completed.returncode == 1


def test_mutation_summary_rejects_missing_metadata(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mutants",
            str(tmp_path / "missing"),
            "--output",
            str(tmp_path / "summary.json"),
            "--require-complete",
        ],
        check=False,
    )

    assert completed.returncode == 1

def test_mutation_summary_accepts_only_allowlisted_survivors(tmp_path: Path) -> None:
    mutants = tmp_path / "mutants"
    _write_meta(mutants, {"survivor": 0, "killed": 1})
    results = tmp_path / "results.txt"
    results.write_text(
        "    specforge_gate.engine.x_demo__mutmut_1: survived\n",
        encoding="utf-8",
    )
    allowed = tmp_path / "allowed.txt"
    allowed.write_text(
        "specforge_gate.engine.x_demo__mutmut_1\n"
        "specforge_gate.engine.x_resolved__mutmut_2\n",
        encoding="utf-8",
    )
    output = tmp_path / "summary.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mutants",
            str(mutants),
            "--results",
            str(results),
            "--allowed-survivors",
            str(allowed),
            "--output",
            str(output),
            "--require-complete",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    summary = json.loads(output.read_text(encoding="utf-8"))
    assert summary["accepted_survivors"] == [
        "specforge_gate.engine.x_demo__mutmut_1"
    ]
    assert summary["unexpected_survivors"] == []
    assert summary["resolved_allowed_survivors"] == [
        "specforge_gate.engine.x_resolved__mutmut_2"
    ]


def test_mutation_summary_rejects_unexpected_survivor(tmp_path: Path) -> None:
    mutants = tmp_path / "mutants"
    _write_meta(mutants, {"survivor": 0})
    results = tmp_path / "results.txt"
    results.write_text(
        "    specforge_gate.engine.x_new__mutmut_9: survived\n",
        encoding="utf-8",
    )
    allowed = tmp_path / "allowed.txt"
    allowed.write_text(
        "specforge_gate.engine.x_known__mutmut_1\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mutants",
            str(mutants),
            "--results",
            str(results),
            "--allowed-survivors",
            str(allowed),
            "--output",
            str(tmp_path / "summary.json"),
            "--require-complete",
        ],
        check=False,
    )

    assert completed.returncode == 1

