from __future__ import annotations

from fastapi.testclient import TestClient

from specforge_gate.api import app
from specforge_gate.web_ui import WEB_UI_HTML

CLIENT = TestClient(app)


def test_root_serves_self_contained_zero_install_ui() -> None:
    response = CLIENT.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "SpecForge Gate — Requirements check" in response.text
    assert 'id="spec-input"' in response.text
    assert 'id="run-check"' in response.text
    assert 'id="run-ai-review"' in response.text
    assert 'id="copy-markdown"' in response.text
    assert 'id="finding-filters"' in response.text
    assert 'id="ai-review-section"' in response.text
    assert 'id="contradictions-list"' in response.text
    assert 'id="improved-spec-output"' in response.text
    assert 'id="draft-gate-status"' in response.text
    assert 'id="draft-gate-detail"' in response.text


def test_web_ui_is_same_origin_and_has_no_external_runtime_assets() -> None:
    lowered = WEB_UI_HTML.casefold()

    assert "https://" not in lowered
    assert "http://" not in lowered
    assert "<script src=" not in lowered
    assert "<link " not in lowered
    assert ".innerhtml" not in lowered
    assert 'fetch("/v1/check"' in lowered
    assert 'fetch("/v1/ai/status"' in lowered
    assert 'fetch("/v1/ai/review"' in lowered
    assert "document.createelement" in lowered
    assert ".textcontent" in lowered


def test_web_ui_has_security_and_no_store_headers() -> None:
    response = CLIENT.get("/")

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-content-type-options"] == "nosniff"
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


def test_web_ui_exposes_deterministic_and_explicit_ai_actions_separately() -> None:
    assert 'id="run-check"' in WEB_UI_HTML
    assert 'id="run-ai-review" type="button" disabled' in WEB_UI_HTML
    assert "async function runAnalysis()" in WEB_UI_HTML
    assert "async function runAIReview()" in WEB_UI_HTML
    assert 'fetch("/v1/check"' in WEB_UI_HTML
    assert 'fetch("/v1/ai/review"' in WEB_UI_HTML
    assert "runButton.addEventListener(\"click\", runAnalysis)" in WEB_UI_HTML
    assert "aiReviewButton.addEventListener(\"click\", runAIReview)" in WEB_UI_HTML
    assert "Analyze requirements never calls AI" in WEB_UI_HTML


def test_web_ui_exposes_ai_status_contradictions_and_reviewable_draft() -> None:
    assert 'id="ai-provider-status"' in WEB_UI_HTML
    assert 'id="ai-provider-detail"' in WEB_UI_HTML
    assert 'id="refresh-ai-status"' in WEB_UI_HTML
    assert 'fetch("/v1/ai/status"' in WEB_UI_HTML
    assert 'id="contradictions-list"' in WEB_UI_HTML
    assert 'id="copy-improved"' in WEB_UI_HTML
    assert 'id="use-improved"' in WEB_UI_HTML
    assert "improvedSpecOutput.textContent = aiReview.improved_spec" in WEB_UI_HTML
    assert "aiReview.draft_deterministic" in WEB_UI_HTML
    assert "Original findings:" in WEB_UI_HTML
    assert "Draft findings:" in WEB_UI_HTML
    assert "navigator.clipboard.writeText(aiReview.improved_spec)" in WEB_UI_HTML
    assert "input.value = draft" in WEB_UI_HTML
    assert "resetReport();" in WEB_UI_HTML
    assert "resetAIReview();" in WEB_UI_HTML


def test_web_ui_exposes_all_finding_filters_and_markdown_copy() -> None:
    for severity in ("all", "error", "warning", "info"):
        assert f'data-filter="{severity}"' in WEB_UI_HTML

    assert "function markdownReport(value)" in WEB_UI_HTML
    assert "navigator.clipboard.writeText(markdownReport(report))" in WEB_UI_HTML
    assert "| Severity | Count |" in WEB_UI_HTML
    assert "**Suggested fix:**" in WEB_UI_HTML


def test_web_ui_route_stays_out_of_openapi_contract() -> None:
    schema = CLIENT.get("/openapi.json").json()

    assert "/" not in schema["paths"]
    assert set(schema["paths"]) == {
        "/healthz",
        "/v1/check",
        "/v1/ai/status",
        "/v1/ai/review",
    }
