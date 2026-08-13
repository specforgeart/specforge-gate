"""SpecForge Gate package."""

from .engine import analyze_text
from .models import AnalysisReport, Finding, Severity, Status

__all__ = ["AnalysisReport", "Finding", "Severity", "Status", "analyze_text"]
__version__ = "0.3.2"
