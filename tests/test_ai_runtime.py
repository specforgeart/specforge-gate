from __future__ import annotations

import pytest

from specforge_gate.ai import AIProviderError, AIProviderErrorCode
from specforge_gate.ai.ollama import OllamaProvider
from specforge_gate.ai.openai_compatible import OpenAICompatibleProvider
from specforge_gate.ai.runtime import provider_from_environment


def test_runtime_is_disabled_without_explicit_provider() -> None:
    assert provider_from_environment({}) is None
    assert provider_from_environment({"SPECFORGE_AI_PROVIDER": "   "}) is None


def test_runtime_builds_ollama_with_safe_local_default() -> None:
    provider = provider_from_environment(
        {
            "SPECFORGE_AI_PROVIDER": "ollama",
            "SPECFORGE_AI_MODEL": "qwen3:8b",
        }
    )

    assert isinstance(provider, OllamaProvider)
    assert provider.model == "qwen3:8b"
    assert provider.base_url == "http://127.0.0.1:11434"
    assert provider.timeout == 60.0


def test_runtime_builds_explicit_openai_compatible_provider() -> None:
    provider = provider_from_environment(
        {
            "SPECFORGE_AI_PROVIDER": "openai-compatible",
            "SPECFORGE_AI_MODEL": "example-model",
            "SPECFORGE_AI_BASE_URL": "https://example.test/v1",
            "SPECFORGE_AI_API_KEY": "secret-value",
            "SPECFORGE_AI_TIMEOUT_SECONDS": "12.5",
        }
    )

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "example-model"
    assert provider.base_url == "https://example.test/v1"
    assert provider.timeout == 12.5
    assert not hasattr(provider, "api_key")


@pytest.mark.parametrize(
    ("environment", "message"),
    [
        ({"SPECFORGE_AI_PROVIDER": "ollama"}, "SPECFORGE_AI_MODEL"),
        (
            {
                "SPECFORGE_AI_PROVIDER": "openai-compatible",
                "SPECFORGE_AI_MODEL": "model",
            },
            "SPECFORGE_AI_BASE_URL",
        ),
        (
            {
                "SPECFORGE_AI_PROVIDER": "other",
                "SPECFORGE_AI_MODEL": "model",
            },
            "SPECFORGE_AI_PROVIDER",
        ),
        (
            {
                "SPECFORGE_AI_PROVIDER": "ollama",
                "SPECFORGE_AI_MODEL": "model",
                "SPECFORGE_AI_TIMEOUT_SECONDS": "zero",
            },
            "SPECFORGE_AI_TIMEOUT_SECONDS",
        ),
        (
            {
                "SPECFORGE_AI_PROVIDER": "ollama",
                "SPECFORGE_AI_MODEL": "model",
                "SPECFORGE_AI_TIMEOUT_SECONDS": "0",
            },
            "SPECFORGE_AI_TIMEOUT_SECONDS",
        ),
    ],
)
def test_runtime_rejects_invalid_configuration(
    environment: dict[str, str],
    message: str,
) -> None:
    with pytest.raises(AIProviderError, match=message) as caught:
        provider_from_environment(environment)

    assert caught.value.code is AIProviderErrorCode.CONFIGURATION
    assert caught.value.retryable is False


def test_runtime_construction_performs_no_network(monkeypatch) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("network must not be used during provider construction")

    monkeypatch.setattr("urllib.request.urlopen", fail_network)

    provider = provider_from_environment(
        {
            "SPECFORGE_AI_PROVIDER": "ollama",
            "SPECFORGE_AI_MODEL": "local-model",
        }
    )

    assert isinstance(provider, OllamaProvider)
