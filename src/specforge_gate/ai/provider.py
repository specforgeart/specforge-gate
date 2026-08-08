"""Provider-neutral contracts for the optional AI analysis layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class AIResponseFormat(StrEnum):
    """Response modes that provider adapters may support."""

    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class AIRequest:
    """Provider-neutral generation request built by optional AI features."""

    system_prompt: str
    user_prompt: str
    response_format: AIResponseFormat = AIResponseFormat.TEXT


@dataclass(frozen=True, slots=True)
class AIResponse:
    """Normalized text response returned by an AI provider adapter."""

    text: str
    provider: str
    model: str


class AIProviderErrorCode(StrEnum):
    """Stable provider failure categories for adapter implementations."""

    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    REQUEST_REJECTED = "request_rejected"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"


class AIProviderError(RuntimeError):
    """Normalized provider failure without transport-specific exception leakage."""

    def __init__(
        self,
        *,
        code: AIProviderErrorCode,
        provider: str,
        message: str,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.provider = provider
        self.retryable = retryable


@runtime_checkable
class AIProvider(Protocol):
    """Structural contract implemented by optional provider adapters."""

    @property
    def provider_id(self) -> str:
        """Stable provider adapter identifier, such as ``ollama``."""
        ...

    @property
    def model(self) -> str:
        """Provider model identifier used for requests."""
        ...

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate one normalized response for a provider-neutral request."""
        ...
