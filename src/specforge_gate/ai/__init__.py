"""Public contracts for SpecForge Gate's optional AI layer."""

from .contradictions import (
    Contradiction,
    ContradictionAnalysis,
    ContradictionAnalysisError,
    ContradictionAnalysisErrorCode,
    analyze_contradictions,
)
from .ollama import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider
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
    "Contradiction",
    "ContradictionAnalysis",
    "ContradictionAnalysisError",
    "ContradictionAnalysisErrorCode",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "analyze_contradictions",
]
