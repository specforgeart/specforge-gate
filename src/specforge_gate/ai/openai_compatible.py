"""OpenAI-compatible chat-completions adapter for SpecForge Gate."""

from __future__ import annotations

import json
import math
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

_DEFAULT_TIMEOUT_SECONDS = 60.0
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class OpenAICompatibleProvider:
    """Synchronous adapter for an explicit OpenAI-compatible API root."""

    provider_id = "openai-compatible"

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = _validate_model(model)
        self._base_url = _normalize_base_url(base_url)
        self._api_key = _validate_api_key(api_key)
        self._timeout = _validate_timeout(timeout)

    @property
    def model(self) -> str:
        """Configured model identifier."""
        return self._model

    @property
    def base_url(self) -> str:
        """Normalized OpenAI-compatible API root."""
        return self._base_url

    @property
    def timeout(self) -> float:
        """Request timeout in seconds."""
        return self._timeout

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate one non-streaming response through chat completions."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "stream": False,
        }
        if request.response_format is AIResponseFormat.JSON:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if self._api_key is not None:
            headers["Authorization"] = f"Bearer {self._api_key}"

        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        http_request = urlrequest.Request(
            f"{self._base_url}/chat/completions",
            data=body,
            headers=headers,
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
                message="OpenAI-compatible request timed out.",
                retryable=True,
            ) from exc
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AIProviderError(
                    code=AIProviderErrorCode.TIMEOUT,
                    provider=self.provider_id,
                    message="OpenAI-compatible request timed out.",
                    retryable=True,
                ) from exc
            raise AIProviderError(
                code=AIProviderErrorCode.UNAVAILABLE,
                provider=self.provider_id,
                message="OpenAI-compatible endpoint is unavailable.",
                retryable=True,
            ) from exc

        if len(raw) > _MAX_RESPONSE_BYTES:
            raise AIProviderError(
                code=AIProviderErrorCode.INVALID_RESPONSE,
                provider=self.provider_id,
                message="OpenAI-compatible response exceeded the supported size limit.",
            )

        return self._decode_response(raw)

    def _decode_response(self, raw: bytes) -> AIResponse:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _invalid_response("OpenAI-compatible endpoint returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise _invalid_response("OpenAI-compatible endpoint returned an unexpected object.")

        model = payload.get("model")
        choices = payload.get("choices")
        if not isinstance(model, str) or not model or not isinstance(choices, list) or not choices:
            raise _invalid_response("OpenAI-compatible response is missing required fields.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise _invalid_response("OpenAI-compatible response has an invalid first choice.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise _invalid_response("OpenAI-compatible response is missing an assistant message.")
        content = message.get("content")
        if not isinstance(content, str):
            raise _invalid_response("OpenAI-compatible response is missing assistant content.")

        return AIResponse(text=content, provider=self.provider_id, model=model)


def _configuration_error(message: str) -> AIProviderError:
    return AIProviderError(
        code=AIProviderErrorCode.CONFIGURATION,
        provider="openai-compatible",
        message=message,
    )


def _validate_model(model: str) -> str:
    value = model.strip()
    if not value:
        raise _configuration_error("OpenAI-compatible model must not be empty.")
    return value


def _validate_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    value = api_key.strip()
    if not value:
        raise _configuration_error("OpenAI-compatible api_key must not be empty when supplied.")
    if "\r" in value or "\n" in value:
        raise _configuration_error("OpenAI-compatible api_key contains invalid characters.")
    return value


def _validate_timeout(timeout: float) -> float:
    value = float(timeout)
    if not math.isfinite(value) or value <= 0:
        raise _configuration_error("OpenAI-compatible timeout must be a positive finite number.")
    return value


def _normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    parsed = parse.urlsplit(value)
    try:
        _ = parsed.port
    except ValueError as exc:
        raise _configuration_error("OpenAI-compatible base_url contains an invalid port.") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise _configuration_error(
            "OpenAI-compatible base_url must be an http(s) API root without credentials, "
            "query, or fragment."
        )
    return value


def _invalid_response(message: str) -> AIProviderError:
    return AIProviderError(
        code=AIProviderErrorCode.INVALID_RESPONSE,
        provider="openai-compatible",
        message=message,
    )


def _http_error(status: int) -> AIProviderError:
    if status in {401, 403}:
        return AIProviderError(
            code=AIProviderErrorCode.AUTHENTICATION,
            provider="openai-compatible",
            message="OpenAI-compatible endpoint rejected authentication.",
        )
    if status == 408:
        return AIProviderError(
            code=AIProviderErrorCode.TIMEOUT,
            provider="openai-compatible",
            message="OpenAI-compatible endpoint timed out the request.",
            retryable=True,
        )
    if status == 429:
        return AIProviderError(
            code=AIProviderErrorCode.RATE_LIMITED,
            provider="openai-compatible",
            message="OpenAI-compatible endpoint rate limited the request.",
            retryable=True,
        )
    if 400 <= status < 500:
        return AIProviderError(
            code=AIProviderErrorCode.REQUEST_REJECTED,
            provider="openai-compatible",
            message=f"OpenAI-compatible endpoint rejected the request with HTTP {status}.",
        )
    return AIProviderError(
        code=AIProviderErrorCode.UNAVAILABLE,
        provider="openai-compatible",
        message=f"OpenAI-compatible endpoint returned HTTP {status}.",
        retryable=True,
    )
