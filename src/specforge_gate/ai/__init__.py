"""Public contracts for SpecForge Gate's optional AI layer."""

from .ollama import OllamaProvider
from .provider import (
    AIProvider,
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIResponseFormat,
)

__all__ = [
    "AIProvider",
    "AIProviderError",
    "AIProviderErrorCode",
    "AIRequest",
    "AIResponse",
    "AIResponseFormat",
    "OllamaProvider",
]
