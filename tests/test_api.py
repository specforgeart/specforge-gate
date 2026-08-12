from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from specforge_gate import __version__
from specforge_gate.ai import (
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
)
from specforge_gate.api import AI_MAX_TEXT_CHARS, app, create_app
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


class SequenceProvider:
    provider_id = "fake"
    model = "fake-model"

    def __init__(self, responses: list[AIResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected provider call")
        return self.responses.pop(0)


class RaisingProvider:
    provider_id = "fake"
    model = "fake-model"

    def __init__(self, error: AIProviderError) -> None:
        self.error = error
        self.calls = 0

    def generate(self, request: AIRequest) -> AIResponse:
        self.calls += 1
        raise self.error


def _response(text: str, *, provider: str = "fake", model: str = "fake-model") -> AIResponse:
    return AIResponse(text=text, provider=provider, model=model)


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


def test_request_body_is_not_persisted_or_logged(tmp_path: Path, monkeypatch, caplog) -> None:
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


def test_app_rejects_ambiguous_ai_provider_configuration() -> None:
    provider = SequenceProvider([])
    with pytest.raises(ValueError, match="mutually exclusive"):
        create_app(ai_provider=provider, ai_provider_from_env=True)


def test_ai_status_is_disabled_without_provider() -> None:
    client = TestClient(create_app())

    response = client.get("/v1/ai/status")

    assert response.status_code == 200
    assert response.json() == {"enabled": False, "provider": None, "model": None}


def test_ai_status_exposes_provider_identity_without_secrets() -> None:
    provider = SequenceProvider([])
    client = TestClient(create_app(ai_provider=provider))

    response = client.get("/v1/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "provider": "fake",
        "model": "fake-model",
    }
    assert "key" not in response.text.lower()


def test_ai_status_rejects_invalid_server_environment(monkeypatch) -> None:
    monkeypatch.setenv("SPECFORGE_AI_PROVIDER", "ollama")
    monkeypatch.delenv("SPECFORGE_AI_MODEL", raising=False)
    client = TestClient(create_app(ai_provider_from_env=True))

    response = client.get("/v1/ai/status")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "ai_provider_configuration"
    assert response.json()["detail"]["provider"] == "ollama"


def test_ai_review_rejects_request_supplied_credentials() -> None:
    provider = SequenceProvider([])
    client = TestClient(create_app(ai_provider=provider))

    response = client.post(
        "/v1/ai/review",
        json={"text": VALID_TEXT, "api_key": "must-not-be-accepted"},
    )

    assert response.status_code == 422
    assert "extra_forbidden" in response.text
    assert provider.requests == []


def test_ai_review_runs_deterministic_contradictions_and_draft_in_order() -> None:
    contradiction_payload = json.dumps(
        {
            "contradictions": [
                {
                    "statement_a": "Ship export.",
                    "statement_b": "A CSV export exists.",
                    "explanation": "Example advisory conflict for transport testing.",
                }
            ]
        }
    )
    provider = SequenceProvider(
        [
            _response(contradiction_payload),
            _response(
                "# Goal\nShip a CSV export.\n\n# Open questions\n- TODO: resolve the conflict."
            ),
        ]
    )
    client = TestClient(create_app(ai_provider=provider))

    response = client.post(
        "/v1/ai/review",
        json={"text": VALID_TEXT, "source": "ai-example.md"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deterministic"] == analyze_text(
        VALID_TEXT,
        source="ai-example.md",
    ).to_dict()
    assert payload["provider"] == "fake"
    assert payload["model"] == "fake-model"
    assert payload["contradictions"] == [
        {
            "statement_a": "Ship export.",
            "statement_b": "A CSV export exists.",
            "explanation": "Example advisory conflict for transport testing.",
        }
    ]
    assert payload["improved_spec"].startswith("# Goal")
    assert len(provider.requests) == 2
    assert provider.requests[0].response_format.value == "json"
    assert provider.requests[1].response_format.value == "text"


def test_ai_review_is_explicit_and_does_not_change_regular_check_path() -> None:
    provider = SequenceProvider([])
    client = TestClient(create_app(ai_provider=provider))

    response = client.post("/v1/check", json={"text": VALID_TEXT})

    assert response.status_code == 200
    assert provider.requests == []


def test_ai_review_requires_server_side_provider_configuration() -> None:
    client = TestClient(create_app())

    response = client.post("/v1/ai/review", json={"text": VALID_TEXT})

    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "ai_not_configured"}}


def test_ai_review_enforces_feature_text_limit_before_provider_call() -> None:
    provider = SequenceProvider([])
    client = TestClient(create_app(ai_provider=provider))

    response = client.post(
        "/v1/ai/review",
        json={"text": "x" * (AI_MAX_TEXT_CHARS + 1)},
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": {"code": "text_too_large", "max_chars": AI_MAX_TEXT_CHARS}
    }
    assert provider.requests == []


def test_ai_review_maps_provider_timeout_without_leaking_request_body() -> None:
    provider = RaisingProvider(
        AIProviderError(
            code=AIProviderErrorCode.TIMEOUT,
            provider="fake",
            message="provider request timed out",
            retryable=True,
        )
    )
    client = TestClient(create_app(ai_provider=provider))

    response = client.post("/v1/ai/review", json={"text": VALID_TEXT})

    assert response.status_code == 504
    assert response.json() == {
        "detail": {
            "code": "ai_provider_timeout",
            "provider": "fake",
            "message": "provider request timed out",
            "retryable": True,
        }
    }
    assert VALID_TEXT not in response.text
    assert provider.calls == 1


def test_ai_review_rejects_invalid_contradiction_output_as_bad_gateway() -> None:
    provider = SequenceProvider([_response("not-json")])
    client = TestClient(create_app(ai_provider=provider))

    response = client.post("/v1/ai/review", json={"text": VALID_TEXT})

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "ai_contradictions_invalid_output"


def test_ai_review_rejects_provider_identity_change_between_feature_calls() -> None:
    provider = SequenceProvider(
        [
            _response('{"contradictions":[]}', provider="first", model="model-a"),
            _response("# Goal\nKeep the source intent.", provider="second", model="model-b"),
        ]
    )
    client = TestClient(create_app(ai_provider=provider))

    response = client.post("/v1/ai/review", json={"text": VALID_TEXT})

    assert response.status_code == 502
    assert response.json() == {"detail": {"code": "ai_identity_mismatch"}}


def test_openapi_exposes_deterministic_and_explicit_ai_endpoints() -> None:
    schema = CLIENT.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/healthz",
        "/v1/check",
        "/v1/ai/status",
        "/v1/ai/review",
    }
    assert schema["paths"]["/healthz"]["get"]["operationId"] == "healthz"
    assert schema["paths"]["/v1/check"]["post"]["operationId"] == "checkRequirements"
    assert schema["paths"]["/v1/ai/status"]["get"]["operationId"] == "getAIStatus"
    assert (
        schema["paths"]["/v1/ai/review"]["post"]["operationId"]
        == "reviewRequirementsWithAI"
    )


def test_api_dependencies_are_optional_and_mutation_excludes_http_plumbing() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    assert project["project"]["dependencies"] == ["PyYAML>=6.0.2"]
    api_dependencies = project["project"]["optional-dependencies"]["api"]
    dev_dependencies = project["project"]["optional-dependencies"]["dev"]

    assert "fastapi>=0.115,<1" in api_dependencies
    assert "uvicorn>=0.30,<1" in api_dependencies
    assert "httpx2>=2,<3" in dev_dependencies
    assert "httpx>=0.27,<1" not in dev_dependencies
    assert "src/specforge_gate/api.py" in project["tool"]["mutmut"]["do_not_mutate"]
    assert "src/specforge_gate/ai/runtime.py" in project["tool"]["mutmut"]["do_not_mutate"]
