"""Ollama adapter for SpecForge Gate's optional AI provider contract."""

from __future__ import annotations

import json
import math
import socket
from typing import Any
from urllib import error, parse
from urllib import request as urlrequest

from .provider import (
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIResponseFormat,
)

_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_DEFAULT_TIMEOUT_SECONDS = 60.0
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class OllamaProvider:
    """Synchronous non-streaming adapter for Ollama's local HTTP API."""

    provider_id = "ollama"

    def __init__(
        self,
        *,
        model: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = _validate_model(model)
        self._base_url = _normalize_base_url(base_url)
        self._timeout = _validate_timeout(timeout)

    @property
    def model(self) -> str:
        """Configured Ollama model name."""
        return self._model

    @property
    def base_url(self) -> str:
        """Normalized Ollama origin used by this adapter."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Request timeout in seconds."""
        return self._timeout

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate one non-streaming response through ``POST /api/chat``."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
        }
        if request.response_format is AIResponseFormat.JSON:
            payload["format"] = "json"

        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        http_request = urlrequest.Request(
            f"{self._base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(http_request, timeout=self._timeout) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
        except error.HTTPError as exc:
            raise _http_error(exc.code) from exc
        except TimeoutError as exc:
            raise AIProviderError(
                code=AIProviderErrorCode.TIMEOUT,
                provider=self.provider_id,
                message="Ollama request timed out.",
                retryable=True,
            ) from exc
        except error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise AIProviderError(
                    code=AIProviderErrorCode.TIMEOUT,
                    provider=self.provider_id,
                    message="Ollama request timed out.",
                    retryable=True,
                ) from exc
            raise AIProviderError(
                code=AIProviderErrorCode.UNAVAILABLE,
                provider=self.provider_id,
                message="Ollama endpoint is unavailable.",
                retryable=True,
            ) from exc

        if len(raw) > _MAX_RESPONSE_BYTES:
            raise AIProviderError(
                code=AIProviderErrorCode.INVALID_RESPONSE,
                provider=self.provider_id,
                message="Ollama response exceeded the supported size limit.",
            )

        return self._decode_response(raw)

    def _decode_response(self, raw: bytes) -> AIResponse:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _invalid_response("Ollama returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise _invalid_response("Ollama returned an unexpected response object.")

        message = payload.get("message")
        model = payload.get("model")
        if not isinstance(message, dict) or not isinstance(model, str) or not model:
            raise _invalid_response("Ollama response is missing required fields.")

        content = message.get("content")
        if not isinstance(content, str):
            raise _invalid_response("Ollama response is missing assistant content.")

        return AIResponse(text=content, provider=self.provider_id, model=model)


def _configuration_error(message: str) -> AIProviderError:
    return AIProviderError(
        code=AIProviderErrorCode.CONFIGURATION,
        provider="ollama",
        message=message,
    )


def _validate_model(model: str) -> str:
    value = model.strip()
    if not value:
        raise _configuration_error("Ollama model must not be empty.")
    return value


def _validate_timeout(timeout: float) -> float:
    value = float(timeout)
    if not math.isfinite(value) or value <= 0:
        raise _configuration_error("Ollama timeout must be a positive finite number.")
    return value


def _normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    parsed = parse.urlsplit(value)
    try:
        _ = parsed.port
    except ValueError as exc:
        raise _configuration_error("Ollama base_url contains an invalid port.") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise _configuration_error(
            "Ollama base_url must be an http(s) origin without credentials, path, "
            "query, or fragment."
        )
    return value


def _invalid_response(message: str) -> AIProviderError:
    return AIProviderError(
        code=AIProviderErrorCode.INVALID_RESPONSE,
        provider="ollama",
        message=message,
    )


def _http_error(status: int) -> AIProviderError:
    if status in {401, 403}:
        return AIProviderError(
            code=AIProviderErrorCode.AUTHENTICATION,
            provider="ollama",
            message="Ollama rejected authentication.",
        )
    if status == 408:
        return AIProviderError(
            code=AIProviderErrorCode.TIMEOUT,
            provider="ollama",
            message="Ollama timed out the request.",
            retryable=True,
        )
    if status == 429:
        return AIProviderError(
            code=AIProviderErrorCode.RATE_LIMITED,
            provider="ollama",
            message="Ollama rate limited the request.",
            retryable=True,
        )
    if 400 <= status < 500:
        return AIProviderError(
            code=AIProviderErrorCode.REQUEST_REJECTED,
            provider="ollama",
            message=f"Ollama rejected the request with HTTP {status}.",
        )
    return AIProviderError(
        code=AIProviderErrorCode.UNAVAILABLE,
        provider="ollama",
        message=f"Ollama returned HTTP {status}.",
        retryable=True,
    )
