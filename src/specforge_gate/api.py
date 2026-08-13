"""Optional stateless REST API for deterministic and explicit advisory AI analysis."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from specforge_gate import __version__
from specforge_gate.ai import (
    AIProvider,
    AIProviderError,
    AIProviderErrorCode,
    Contradiction,
    ContradictionAnalysisError,
    ContradictionAnalysisErrorCode,
    ImprovedSpecDraftError,
    ImprovedSpecDraftErrorCode,
    analyze_contradictions,
    draft_improved_specification,
)
from specforge_gate.ai.runtime import provider_from_environment
from specforge_gate.config import ProjectConfig, RuleConfig
from specforge_gate.engine import analyze_text
from specforge_gate.models import AnalysisReport, Severity, Status
from specforge_gate.rules import builtin_rules
from specforge_gate.suppression import SuppressionError
from specforge_gate.web_ui import WEB_UI_HEADERS, WEB_UI_HTML

DEFAULT_MAX_TEXT_CHARS = 1_000_000
AI_MAX_TEXT_CHARS = 200_000
MAX_SOURCE_CHARS = 1_024


class ApiRuleConfig(BaseModel):
    """Per-rule API configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    severity: Severity | None = None


class ApiProjectConfig(BaseModel):
    """Inline configuration supported by the stateless API."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    language: Literal["auto", "ru", "en"] = "auto"
    rules: dict[str, ApiRuleConfig] = Field(default_factory=dict)

    @field_validator("rules")
    @classmethod
    def validate_rule_ids(cls, rules: dict[str, ApiRuleConfig]) -> dict[str, ApiRuleConfig]:
        known = {rule.rule_id for rule in builtin_rules()}
        unknown = sorted(set(rules) - known)
        if unknown:
            raise ValueError(f"unknown rule ID: {', '.join(unknown)}")
        return rules

    def to_domain(self) -> ProjectConfig:
        return ProjectConfig(
            version=self.version,
            language=self.language,
            rules={
                rule_id: RuleConfig(enabled=item.enabled, severity=item.severity)
                for rule_id, item in self.rules.items()
            },
        )


class AnalyzeRequest(BaseModel):
    """Single-document deterministic or advisory analysis request."""

    model_config = ConfigDict(extra="forbid")

    text: str
    source: str = Field(default="<api>", min_length=1, max_length=MAX_SOURCE_CHARS)
    config: ApiProjectConfig | None = None


class FindingResponse(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    suggestion: str
    line: int | None = None
    excerpt: str | None = None


class SummaryResponse(BaseModel):
    errors: int
    warnings: int
    info: int
    total: int


class AnalysisResponse(BaseModel):
    source: str
    status: Status
    summary: SummaryResponse
    findings: list[FindingResponse]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["specforge-gate"]
    version: str


class AIStatusResponse(BaseModel):
    enabled: bool
    provider: str | None = None
    model: str | None = None


class ContradictionResponse(BaseModel):
    statement_a: str
    statement_b: str
    explanation: str


class AIReviewResponse(BaseModel):
    deterministic: AnalysisResponse
    draft_deterministic: AnalysisResponse
    provider: str
    model: str
    contradictions: list[ContradictionResponse]
    improved_spec: str


def create_app(
    *,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
    ai_provider: AIProvider | None = None,
    ai_provider_from_env: bool = False,
) -> FastAPI:
    if max_text_chars <= 0:
        raise ValueError("max_text_chars must be greater than zero")
    if ai_provider is not None and ai_provider_from_env:
        raise ValueError("ai_provider and ai_provider_from_env are mutually exclusive")

    app = FastAPI(
        title="SpecForge Gate API",
        version=__version__,
        description="Stateless deterministic checks plus optional explicit advisory AI review.",
    )

    def resolve_ai_provider() -> AIProvider | None:
        if ai_provider is not None:
            return ai_provider
        if not ai_provider_from_env:
            return None
        try:
            return provider_from_environment()
        except AIProviderError as exc:
            raise _provider_http_error(exc) from exc

    @app.get(
        "/",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def web_ui() -> HTMLResponse:
        return HTMLResponse(content=WEB_UI_HTML, headers=WEB_UI_HEADERS)

    @app.get(
        "/healthz",
        response_model=HealthResponse,
        operation_id="healthz",
        tags=["system"],
    )
    def healthz() -> HealthResponse:
        return HealthResponse(status="ok", service="specforge-gate", version=__version__)

    @app.post(
        "/v1/check",
        response_model=AnalysisResponse,
        operation_id="checkRequirements",
        tags=["analysis"],
    )
    def check_requirements(request: AnalyzeRequest) -> AnalysisResponse:
        return _deterministic_analysis(request, max_chars=max_text_chars)

    @app.get(
        "/v1/ai/status",
        response_model=AIStatusResponse,
        operation_id="getAIStatus",
        tags=["ai"],
    )
    def ai_status() -> AIStatusResponse:
        provider = resolve_ai_provider()
        if provider is None:
            return AIStatusResponse(enabled=False)
        return AIStatusResponse(
            enabled=True,
            provider=provider.provider_id,
            model=provider.model,
        )

    @app.post(
        "/v1/ai/review",
        response_model=AIReviewResponse,
        operation_id="reviewRequirementsWithAI",
        tags=["ai"],
    )
    def review_requirements_with_ai(request: AnalyzeRequest) -> AIReviewResponse:
        original_report = _analysis_report(
            request.text,
            request.source,
            request.config,
            max_chars=min(max_text_chars, AI_MAX_TEXT_CHARS),
        )
        deterministic = AnalysisResponse.model_validate(original_report.to_dict())
        provider = resolve_ai_provider()
        if provider is None:
            raise HTTPException(
                status_code=503,
                detail={"code": "ai_not_configured"},
            )
        try:
            contradiction_analysis = analyze_contradictions(request.text, provider)
            draft = draft_improved_specification(
                request.text,
                provider,
                contradictions=contradiction_analysis.contradictions,
                findings=tuple(original_report.findings),
            )
        except AIProviderError as exc:
            raise _provider_http_error(exc) from exc
        except ContradictionAnalysisError as exc:
            raise _contradiction_http_error(exc) from exc
        except ImprovedSpecDraftError as exc:
            raise _draft_http_error(exc) from exc

        draft_report = _analysis_report(
            draft.text,
            f"{request.source}#improved-draft",
            request.config,
            max_chars=max_text_chars,
        )
        draft_deterministic = AnalysisResponse.model_validate(draft_report.to_dict())

        if (
            contradiction_analysis.provider != provider.provider_id
            or draft.provider != provider.provider_id
        ):
            raise HTTPException(
                status_code=502,
                detail={"code": "ai_identity_mismatch"},
            )

        return AIReviewResponse(
            deterministic=deterministic,
            draft_deterministic=draft_deterministic,
            provider=provider.provider_id,
            model=provider.model,
            contradictions=[
                _contradiction_response(item)
                for item in contradiction_analysis.contradictions
            ],
            improved_spec=draft.text,
        )

    return app


def _analysis_report(
    text: str,
    source: str,
    config_value: ApiProjectConfig | None,
    *,
    max_chars: int,
) -> AnalysisReport:
    if len(text) > max_chars:
        raise HTTPException(
            status_code=413,
            detail={"code": "text_too_large", "max_chars": max_chars},
        )
    config = config_value.to_domain() if config_value is not None else ProjectConfig()
    try:
        return analyze_text(text, source=source, config=config)
    except SuppressionError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_suppression",
                "message": str(exc),
                "line": exc.line,
            },
        ) from exc


def _deterministic_analysis(request: AnalyzeRequest, *, max_chars: int) -> AnalysisResponse:
    report = _analysis_report(
        request.text,
        request.source,
        request.config,
        max_chars=max_chars,
    )
    return AnalysisResponse.model_validate(report.to_dict())


def _contradiction_response(item: Contradiction) -> ContradictionResponse:
    return ContradictionResponse(
        statement_a=item.statement_a,
        statement_b=item.statement_b,
        explanation=item.explanation,
    )


def _provider_http_error(exc: AIProviderError) -> HTTPException:
    status_by_code = {
        AIProviderErrorCode.CONFIGURATION: 503,
        AIProviderErrorCode.AUTHENTICATION: 502,
        AIProviderErrorCode.REQUEST_REJECTED: 502,
        AIProviderErrorCode.RATE_LIMITED: 429,
        AIProviderErrorCode.UNAVAILABLE: 503,
        AIProviderErrorCode.TIMEOUT: 504,
        AIProviderErrorCode.INVALID_RESPONSE: 502,
    }
    return HTTPException(
        status_code=status_by_code[exc.code],
        detail={
            "code": f"ai_provider_{exc.code.value}",
            "provider": exc.provider,
            "message": str(exc),
            "retryable": exc.retryable,
        },
    )


def _contradiction_http_error(exc: ContradictionAnalysisError) -> HTTPException:
    status = 422 if exc.code is ContradictionAnalysisErrorCode.INVALID_INPUT else 502
    return HTTPException(
        status_code=status,
        detail={"code": f"ai_contradictions_{exc.code.value}", "message": str(exc)},
    )


def _draft_http_error(exc: ImprovedSpecDraftError) -> HTTPException:
    status = 422 if exc.code is ImprovedSpecDraftErrorCode.INVALID_INPUT else 502
    return HTTPException(
        status_code=status,
        detail={"code": f"ai_draft_{exc.code.value}", "message": str(exc)},
    )


app = create_app(ai_provider_from_env=True)
