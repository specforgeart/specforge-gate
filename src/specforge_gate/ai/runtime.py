"""Server-side runtime configuration for optional SpecForge Gate AI providers."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping

from .ollama import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider
from .provider import AIProvider, AIProviderError, AIProviderErrorCode

_DEFAULT_TIMEOUT_SECONDS = 60.0
_DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def provider_from_environment(
    environ: Mapping[str, str] | None = None,
) -> AIProvider | None:
    """Build the explicitly configured AI provider without performing network I/O."""
    values = os.environ if environ is None else environ
    raw_provider = values.get("SPECFORGE_AI_PROVIDER")
    if raw_provider is None or not raw_provider.strip():
        return None

    provider_id = raw_provider.strip().lower()
    if provider_id not in {"ollama", "openai-compatible"}:
        raise _configuration_error(
            provider_id,
            "SPECFORGE_AI_PROVIDER must be 'ollama' or 'openai-compatible'.",
        )

    model = _required(values, "SPECFORGE_AI_MODEL", provider=provider_id)
    timeout = _timeout(values, provider=provider_id)

    if provider_id == "ollama":
        base_url = values.get("SPECFORGE_AI_BASE_URL", _DEFAULT_OLLAMA_BASE_URL)
        return OllamaProvider(model=model, base_url=base_url, timeout=timeout)

    if provider_id == "openai-compatible":
        base_url = _required(values, "SPECFORGE_AI_BASE_URL", provider=provider_id)
        api_key = values.get("SPECFORGE_AI_API_KEY")
        return OpenAICompatibleProvider(
            model=model,
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
        )

    raise AssertionError("unreachable provider selection")


def _required(values: Mapping[str, str], name: str, *, provider: str) -> str:
    value = values.get(name)
    if value is None or not value.strip():
        raise _configuration_error(provider, f"{name} must be configured.")
    return value.strip()


def _timeout(values: Mapping[str, str], *, provider: str) -> float:
    raw = values.get("SPECFORGE_AI_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return _DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise _configuration_error(
            provider,
            "SPECFORGE_AI_TIMEOUT_SECONDS must be a positive finite number.",
        ) from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise _configuration_error(
            provider,
            "SPECFORGE_AI_TIMEOUT_SECONDS must be a positive finite number.",
        )
    return timeout


def _configuration_error(provider: str, message: str) -> AIProviderError:
    return AIProviderError(
        code=AIProviderErrorCode.CONFIGURATION,
        provider=provider or "runtime",
        message=message,
        retryable=False,
    )
