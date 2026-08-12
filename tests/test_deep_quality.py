from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = "34e114876b0b11c390a56381ad16ebd13914f8d5"
SETUP_PYTHON_SHA = "5fda3b95a4ea91299a34e894583c3862153e4b97"
MUTMUT_VERSION = "3.7.0"


def _yaml(path: str) -> dict[str, Any]:
    return yaml.load((ROOT / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _pyproject() -> dict[str, Any]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_hypothesis_is_development_only() -> None:
    project = _pyproject()["project"]
    runtime = project["dependencies"]
    dev = project["optional-dependencies"]["dev"]

    assert not any(item.lower().startswith("hypothesis") for item in runtime)
    assert "hypothesis>=6.165.2,<7" in dev
    assert not any(item.lower().startswith("mutmut") for item in runtime)
    assert not any(item.lower().startswith("mutmut") for item in dev)


def test_mutmut_scope_targets_deterministic_product_logic() -> None:
    config = _pyproject()["tool"]["mutmut"]

    assert config["source_paths"] == ["src/specforge_gate/"]
    assert config["mutate_only_covered_lines"] is True
    assert config["max_stack_depth"] == 12
    assert set(config["do_not_mutate"]) == {
        "src/specforge_gate/__init__.py",
        "src/specforge_gate/cli.py",
        "src/specforge_gate/github_action.py",
        "src/specforge_gate/api.py",
        "src/specforge_gate/web_ui.py",
        "src/specforge_gate/ai/__init__.py",
        "src/specforge_gate/ai/provider.py",
        "src/specforge_gate/ai/ollama.py",
        "src/specforge_gate/ai/openai_compatible.py",
        "src/specforge_gate/ai/contradictions.py",
    }
    selection = set(config["pytest_add_cli_args_test_selection"])
    assert {
        "tests/test_engine.py",
        "tests/test_config.py",
        "tests/test_suppression.py",
        "tests/test_properties.py",
        "tests/test_mutation_contracts.py",
    } <= selection


def test_mutation_workflow_is_separate_read_only_and_pinned() -> None:
    workflow = _yaml(".github/workflows/mutation-testing.yml")
    triggers = workflow["on"]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["mutation-testing"]
    assert job["runs-on"] == "ubuntu-latest"
    assert int(job["timeout-minutes"]) <= 45
    assert "if" not in job

    text = (ROOT / ".github/workflows/mutation-testing.yml").read_text(encoding="utf-8")
    assert f"actions/checkout@{CHECKOUT_SHA} # v4.3.1" in text
    assert f"actions/setup-python@{SETUP_PYTHON_SHA} # v7.0.0" in text
    assert f'mutmut=={MUTMUT_VERSION}' in text
    assert "mutmut run --max-children 4" in text
    assert "scripts/mutation_summary.py" in text
    assert "--allowed-survivors .github/mutation-allowed-survivors.txt" in text
    assert '"$GITHUB_STEP_SUMMARY"' in text
    assert "Capture surviving mutant diffs" not in text
    assert "mutmut apply" not in text
    assert "pull_request:" not in text


def test_mutation_testing_is_not_a_required_main_context() -> None:
    quality = (ROOT / "docs/quality-gates.md").read_text(encoding="utf-8")
    required_section = quality.split("## Main branch protection", 1)[1]
    required_bullets = set(re.findall(r"^- `([^`]+)`$", required_section, flags=re.MULTILINE))
    assert "mutation-testing" not in required_bullets
    assert required_bullets == {
        "ci-gate",
        "windows-quality",
        "action-smoke",
        "pr-policy",
        "dependency-review",
        "CodeQL",
    }


def test_final_mutation_baseline_and_allowlist_are_recorded() -> None:
    baseline = (ROOT / "docs/mutation-baseline.md").read_text(encoding="utf-8")
    assert "Status: FINAL" in baseline
    assert "DO NOT MERGE" not in baseline
    assert "run `31181702170`" in baseline
    assert "implementation head: `abcbc261b0e19f238632146ae58c1116173213fc`" in baseline
    assert "total mutants: **495**" in baseline
    assert "killed: **486**" in baseline
    assert "survived: **9**" in baseline
    assert "**98.18%**" in baseline
    assert "15 behavior-changing survivors" in baseline
    assert "nine accepted survivors" in baseline

    allowed = set(
        (ROOT / ".github/mutation-allowed-survivors.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert allowed == {
        "specforge_gate.reporters.x_render_json__mutmut_2",
        "specforge_gate.engine.x_analyze_text__mutmut_44",
        "specforge_gate.config.x_load_project_config__mutmut_8",
        "specforge_gate.config.x_load_project_config__mutmut_10",
        "specforge_gate.config.x__validate_config__mutmut_111",
        "specforge_gate.suppression.x_parse_suppressions__mutmut_12",
        "specforge_gate.suppression.x_parse_suppressions__mutmut_23",
        "specforge_gate.suppression.x_parse_suppressions__mutmut_38",
        "specforge_gate.suppression.x_parse_suppressions__mutmut_52",
    }


def test_gitignore_excludes_property_and_mutation_caches() -> None:
    ignored = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
    assert {".hypothesis/", "mutants/", "mutation-results.txt", "mutation-summary.json"} <= ignored
