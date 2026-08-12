from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "demo_local_ai.py"
DEMO = ROOT / "examples" / "ai" / "local-provider-demo.md"

STATEMENT_A = "The export must complete within 2 seconds."
STATEMENT_B = "The export may take up to 30 seconds."


class FakeOllamaHandler(BaseHTTPRequestHandler):
    model = "demo-model"
    requests: ClassVar[list[dict[str, object]]] = []

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path != "/api/tags":
            self.send_error(404)
            return
        self._json_response(
            {
                "models": [
                    {
                        "name": self.model,
                        "model": self.model,
                    }
                ]
            }
        )

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_error(404)
            return

        length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.requests.append(payload)

        if payload.get("format") == "json":
            content = json.dumps(
                {
                    "contradictions": [
                        {
                            "statement_a": STATEMENT_A,
                            "statement_b": STATEMENT_B,
                            "explanation": "The two completion limits conflict.",
                        }
                    ]
                }
            )
        else:
            content = (
                "# Goal\n\n"
                "Export the selected orders to CSV.\n\n"
                "# Open questions\n\n"
                "- TODO: resolve the conflicting completion-time limits."
            )

        self._json_response(
            {
                "model": self.model,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "done": True,
            }
        )

    def _json_response(self, payload: object) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _server() -> tuple[ThreadingHTTPServer, threading.Thread]:
    FakeOllamaHandler.requests.clear()
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_local_ai_demo_runs_full_cli_flow_through_local_http_provider() -> None:
    server, thread = _server()
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                FakeOllamaHandler.model,
                "--file",
                str(DEMO),
                "--format",
                "json",
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert result.returncode == 0, result.stderr
    assert "== Deterministic gate (no provider call) ==" in result.stdout
    assert "== Advisory AI review via Ollama ==" in result.stdout
    assert '"provider": "ollama"' in result.stdout
    assert '"model": "demo-model"' in result.stdout
    assert STATEMENT_A in result.stdout
    assert STATEMENT_B in result.stdout
    assert '"improved_spec": "# Goal' in result.stdout

    assert len(FakeOllamaHandler.requests) == 2
    assert FakeOllamaHandler.requests[0]["format"] == "json"
    assert "format" not in FakeOllamaHandler.requests[1]


def test_local_ai_demo_reports_missing_model_without_chat_request() -> None:
    server, thread = _server()
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "missing-model",
                "--file",
                str(DEMO),
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert result.returncode == 2
    assert "Ollama model is not installed: missing-model" in result.stderr
    assert "ollama pull missing-model" in result.stderr
    assert FakeOllamaHandler.requests == []


def test_local_ai_demo_fixture_contains_direct_contradiction() -> None:
    text = DEMO.read_text(encoding="utf-8")

    assert STATEMENT_A in text
    assert STATEMENT_B in text
    assert "# Goal" in text
    assert "# Acceptance criteria" in text
    assert "# Out of scope" in text
    assert "# Errors and edge cases" in text
