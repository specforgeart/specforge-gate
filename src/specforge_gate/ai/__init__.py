"""Public contracts for SpecForge Gate's optional AI layer."""

from .contradictions import (
    Contradiction,
    ContradictionAnalysis,
    ContradictionAnalysisError,
    ContradictionAnalysisErrorCode,
    analyze_contradictions,
)
from .fidelity import (
    DraftFidelityFinding,
    DraftFidelityReport,
    DraftFidelityStatus,
    analyze_draft_fidelity,
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
    "DraftFidelityFinding",
    "DraftFidelityReport",
    "DraftFidelityStatus",
    "ImprovedSpecDraft",
    "ImprovedSpecDraftError",
    "ImprovedSpecDraftErrorCode",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "analyze_contradictions",
    "analyze_draft_fidelity",
    "draft_improved_specification",
]
