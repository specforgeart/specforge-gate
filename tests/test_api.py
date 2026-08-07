from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from specforge_gate import __version__
from specforge_gate.api import app, create_app
from specforge_gate.engine import analyze_text

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)

VALID_TEXT = """# Goal
Ship export.

# Expected result
A CSV export exists.

# Acceptance criteria
- Given data, when export runs, then a CSV is returned.

# Out of scope
- PDF export.

# Errors and edge cases
- Empty result sets.
"""


def test_healthz_is_stable_and_versioned() -> None:
    response = CLIENT.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "specforge-gate",
        "version": __version__,
    }


def test_check_matches_the_deterministic_core_contract() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={"text": VALID_TEXT, "source": "api-example.md"},
    )

    assert response.status_code == 200
    assert response.json() == analyze_text(VALID_TEXT, source="api-example.md").to_dict()



def test_check_accepts_non_ascii_utf8_text_and_source_label() -> None:
    text = VALID_TEXT + "\nПримечание: экспорт для клиента.\n"

    response = CLIENT.post(
        "/v1/check",
        json={"text": text, "source": "требования.md"},
    )

    assert response.status_code == 200
    assert response.json() == analyze_text(text, source="требования.md").to_dict()


def test_check_returns_findings_without_http_failure() -> None:
    response = CLIENT.post("/v1/check", json={"text": "Need it fast."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "NEEDS WORK"
    assert payload["summary"]["errors"] == 3
    assert payload["summary"]["warnings"] >= 3
    assert payload["summary"]["total"] == len(payload["findings"])


def test_inline_config_can_disable_and_override_rules() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={
            "text": "Need it fast.",
            "config": {
                "version": 1,
                "language": "en",
                "rules": {
                    "SG001": {"enabled": False},
                    "SG101": {"severity": "error"},
                },
            },
        },
    )

    assert response.status_code == 200
    findings = response.json()["findings"]
    assert all(item["rule_id"] != "SG001" for item in findings)
    sg101 = [item for item in findings if item["rule_id"] == "SG101"]
    assert sg101 and all(item["severity"] == "error" for item in sg101)


def test_unknown_rule_id_is_rejected_before_analysis() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={"text": VALID_TEXT, "config": {"rules": {"SG999": {}}}},
    )

    assert response.status_code == 422
    assert "unknown rule ID: SG999" in response.text


def test_filesystem_exclude_config_is_not_part_of_stateless_api() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={"text": VALID_TEXT, "config": {"exclude": ["docs/**"]}},
    )

    assert response.status_code == 422
    assert "extra_forbidden" in response.text


def test_malformed_suppression_has_deterministic_error_shape() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={"text": "<!-- specgate-ignore-next-line -->\n# Goal"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "code": "invalid_suppression",
            "message": "suppression directive requires at least one rule ID",
            "line": 1,
        }
    }



def test_request_body_is_not_persisted_or_logged(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    monkeypatch.chdir(tmp_path)

    response = CLIENT.post(
        "/v1/check",
        json={"text": VALID_TEXT, "source": "sensitive-ticket.md"},
    )

    assert response.status_code == 200
    assert list(tmp_path.iterdir()) == []
    assert VALID_TEXT not in caplog.text


def test_request_rejects_unknown_top_level_fields() -> None:
    response = CLIENT.post(
        "/v1/check",
        json={"text": VALID_TEXT, "path": "secret.md"},
    )

    assert response.status_code == 422
    assert "extra_forbidden" in response.text


def test_request_enforces_configured_text_size_limit() -> None:
    client = TestClient(create_app(max_text_chars=8))

    accepted = client.post("/v1/check", json={"text": "x" * 8})
    rejected = client.post("/v1/check", json={"text": "x" * 9})

    assert accepted.status_code == 200
    assert rejected.status_code == 413
    assert rejected.json() == {
        "detail": {"code": "text_too_large", "max_chars": 8}
    }


def test_app_rejects_non_positive_text_limit() -> None:
    with pytest.raises(ValueError, match="max_text_chars must be greater than zero"):
        create_app(max_text_chars=0)


def test_openapi_exposes_only_the_intended_product_endpoints() -> None:
    schema = CLIENT.get("/openapi.json").json()

    assert set(schema["paths"]) == {"/healthz", "/v1/check"}
    assert schema["paths"]["/healthz"]["get"]["operationId"] == "healthz"
    assert schema["paths"]["/v1/check"]["post"]["operationId"] == "checkRequirements"


def test_api_dependencies_are_optional_and_mutation_excludes_http_plumbing() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    assert project["project"]["dependencies"] == ["PyYAML>=6.0.2"]
    assert "fastapi>=0.115,<1" in project["project"]["optional-dependencies"]["api"]
    assert "uvicorn>=0.30,<1" in project["project"]["optional-dependencies"]["api"]
    assert "src/specforge_gate/api.py" in project["tool"]["mutmut"]["do_not_mutate"]
