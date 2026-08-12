"""Public contracts for SpecForge Gate's optional AI layer."""

from .contradictions import (
    Contradiction,
    ContradictionAnalysis,
    ContradictionAnalysisError,
    ContradictionAnalysisErrorCode,
    analyze_contradictions,
)
from .improved_draft import (
    ImprovedSpecDraft,
    ImprovedSpecDraftError,
    ImprovedSpecDraftErrorCode,
    draft_improved_specification,
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
    "ImprovedSpecDraft",
    "ImprovedSpecDraftError",
    "ImprovedSpecDraftErrorCode",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "analyze_contradictions",
    "draft_improved_specification",
]
