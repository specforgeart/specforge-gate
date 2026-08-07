"""Optional stateless REST API for the deterministic analysis core."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from specforge_gate import __version__
from specforge_gate.config import ProjectConfig, RuleConfig
from specforge_gate.engine import analyze_text
from specforge_gate.models import Severity, Status
from specforge_gate.rules import builtin_rules
from specforge_gate.suppression import SuppressionError

DEFAULT_MAX_TEXT_CHARS = 1_000_000
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
    """Single-document deterministic analysis request."""

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


def create_app(*, max_text_chars: int = DEFAULT_MAX_TEXT_CHARS) -> FastAPI:
    if max_text_chars <= 0:
        raise ValueError("max_text_chars must be greater than zero")

    app = FastAPI(
        title="SpecForge Gate API",
        version=__version__,
        description="Stateless REST interface for the deterministic SpecForge Gate core.",
    )

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
        if len(request.text) > max_text_chars:
            raise HTTPException(
                status_code=413,
                detail={"code": "text_too_large", "max_chars": max_text_chars},
            )
        config = request.config.to_domain() if request.config is not None else ProjectConfig()
        try:
            report = analyze_text(request.text, source=request.source, config=config)
        except SuppressionError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_suppression",
                    "message": str(exc),
                    "line": exc.line,
                },
            ) from exc
        return AnalysisResponse.model_validate(report.to_dict())

    return app


app = create_app()
