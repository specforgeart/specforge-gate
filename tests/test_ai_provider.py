from __future__ import annotations

import ast
import tomllib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import specforge_gate.ai as ai
from specforge_gate.ai import (
    AIProvider,
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIResponseFormat,
)

ROOT = Path(__file__).resolve().parents[1]
CORE_MODULES = {
    "config.py",
    "document.py",
    "engine.py",
    "models.py",
    "reporters.py",
    "suppression.py",
}


class FakeProvider:
    provider_id = "fake"
    model = "fake-model"

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            text=f"echo:{request.user_prompt}",
            provider=self.provider_id,
            model=self.model,
        )


class IncompleteProvider:
    provider_id = "incomplete"
    model = "none"


def test_request_defaults_to_text_and_is_immutable() -> None:
    request = AIRequest(system_prompt="system", user_prompt="user")

    assert request == AIRequest(
        system_prompt="system",
        user_prompt="user",
        response_format=AIResponseFormat.TEXT,
    )
    with pytest.raises(FrozenInstanceError):
        request.user_prompt = "changed"  # type: ignore[misc]


def test_request_can_ask_for_json_without_provider_specific_options() -> None:
    request = AIRequest(
        system_prompt="Return structured contradictions.",
        user_prompt="Specification text",
        response_format=AIResponseFormat.JSON,
    )

    assert request.response_format.value == "json"
    assert not hasattr(request, "base_url")
    assert not hasattr(request, "api_key")


def test_response_is_normalized_and_immutable() -> None:
    response = AIResponse(text="result", provider="fake", model="fake-model")

    assert response.text == "result"
    assert response.provider == "fake"
    assert response.model == "fake-model"
    with pytest.raises(FrozenInstanceError):
        response.text = "changed"  # type: ignore[misc]


def test_provider_protocol_is_structural_and_runtime_checkable() -> None:
    provider = FakeProvider()

    assert isinstance(provider, AIProvider)
    assert provider.generate(AIRequest("system", "hello")) == AIResponse(
        text="echo:hello",
        provider="fake",
        model="fake-model",
    )
    assert not isinstance(IncompleteProvider(), AIProvider)


def test_provider_error_preserves_normalized_metadata() -> None:
    error = AIProviderError(
        code=AIProviderErrorCode.TIMEOUT,
        provider="fake",
        message="provider request timed out",
        retryable=True,
    )

    assert str(error) == "provider request timed out"
    assert error.code is AIProviderErrorCode.TIMEOUT
    assert error.provider == "fake"
    assert error.retryable is True


def test_provider_error_codes_are_stable_contract() -> None:
    assert [item.value for item in AIProviderErrorCode] == [
        "configuration",
        "authentication",
        "request_rejected",
        "rate_limited",
        "unavailable",
        "timeout",
        "invalid_response",
    ]

def test_ai_package_exports_exact_public_contract() -> None:
    assert ai.__all__ == [
        "AIProvider",
        "AIProviderError",
        "AIProviderErrorCode",
        "AIRequest",
        "AIResponse",
        "AIResponseFormat",
        "Contradiction",
        "ContradictionAnalysis",
        "ContradictionAnalysisError",
        "ContradictionAnalysisErrorCode",
        "ImprovedSpecDraft",
        "ImprovedSpecDraftError",
        "ImprovedSpecDraftErrorCode",
        "OllamaProvider",
        "OpenAICompatibleProvider",
        "analyze_contradictions",
        "draft_improved_specification",
    ]


def test_provider_contract_uses_standard_library_only() -> None:
    path = ROOT / "src/specforge_gate/ai/provider.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots == {"__future__", "dataclasses", "enum", "typing"}


def test_deterministic_core_does_not_import_optional_ai_layer() -> None:
    core = ROOT / "src/specforge_gate"
    for name in CORE_MODULES:
        tree = ast.parse((core / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("specforge_gate.ai") for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith("specforge_gate.ai")


def test_provider_interface_does_not_change_base_runtime_dependencies() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert project["dependencies"] == ["PyYAML>=6.0.2"]

def test_canonical_checks_smoke_import_ai_contract_from_built_wheel() -> None:
    for path in ("scripts/check.ps1", "scripts/check.sh"):
        text = (ROOT / path).read_text(encoding="utf-8-sig")
        assert "from specforge_gate.ai import AIRequest, AIResponseFormat" in text
        assert "request.response_format is AIResponseFormat.TEXT" in text
        assert "from specforge_gate.ai import OllamaProvider" in text
        assert "provider.provider_id == 'ollama'" in text
        assert "from specforge_gate.ai import OpenAICompatibleProvider" in text
        assert "provider.provider_id == 'openai-compatible'" in text
        assert "from specforge_gate.ai import analyze_contradictions" in text
        assert "from specforge_gate.ai import draft_improved_specification" in text

