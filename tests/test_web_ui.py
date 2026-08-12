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
    assert 'id="copy-markdown"' in response.text
    assert 'id="finding-filters"' in response.text
    assert 'fetch("/v1/check"' in response.text


def test_web_ui_is_same_origin_and_has_no_external_runtime_assets() -> None:
    lowered = WEB_UI_HTML.casefold()

    assert "https://" not in lowered
    assert "http://" not in lowered
    assert "<script src=" not in lowered
    assert "<link " not in lowered
    assert ".innerhtml" not in lowered
    assert 'fetch("/v1/check"' in lowered
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
