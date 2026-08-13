from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from specforge_gate.ai import AIRequest, AIResponse, AIResponseFormat
from specforge_gate.cli import main


class SequenceProvider:
    provider_id = "fake"
    model = "fake-model"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)
        text = self.responses[len(self.requests) - 1]
        return AIResponse(
            text=text,
            provider=self.provider_id,
            model=self.model,
        )


def _specification() -> str:
    return """# Goal
Export orders.

# Expected result
A CSV file is downloaded.

# Acceptance criteria
- Export must finish in 2 seconds.
- Export may take up to 30 seconds.

# Out of scope
- PDF export.

# Errors and edge cases
- Empty results produce headers only.
"""


def _provider() -> SequenceProvider:
    contradiction_json = json.dumps(
        {
            "contradictions": [
                {
                    "statement_a": "Export must finish in 2 seconds.",
                    "statement_b": "Export may take up to 30 seconds.",
                    "explanation": "The time limits conflict.",
                }
            ]
        }
    )
    draft = """# Goal

Export orders to CSV.

# Open questions

- TODO: resolve the conflicting export time limits.
"""
    return SequenceProvider([contradiction_json, draft])


def test_ai_review_json_matches_rest_product_shape(
    tmp_path: Path,
    monkeypatch: object,
    capsys: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text(_specification(), encoding="utf-8")
    provider = _provider()
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: provider,
    )

    assert main(["ai-review", str(path), "--format", "json", "--fail-on", "none"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {
        "deterministic",
        "draft_deterministic",
        "provider",
        "model",
        "contradictions",
        "improved_spec",
    }
    assert payload["provider"] == "fake"
    assert payload["model"] == "fake-model"
    assert payload["deterministic"]["source"] == str(path)
    assert payload["draft_deterministic"]["source"] == f"{path}#improved-draft"
    assert payload["contradictions"] == [
        {
            "statement_a": "Export must finish in 2 seconds.",
            "statement_b": "Export may take up to 30 seconds.",
            "explanation": "The time limits conflict.",
        }
    ]
    assert payload["improved_spec"].startswith("# Goal")
    assert [request.response_format for request in provider.requests] == [
        AIResponseFormat.JSON,
        AIResponseFormat.TEXT,
    ]


def test_ai_review_json_survives_cp1251_stdout(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text(_specification(), encoding="utf-8")
    provider = _provider()
    provider.responses[1] = "# Goal\n\nExport orders for M\u00fcnchen \U0001f600 users.\n"
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: provider,
    )

    raw = io.BytesIO()
    stdout = io.TextIOWrapper(raw, encoding="cp1251", newline="\n")
    monkeypatch.setattr(sys, "stdout", stdout)

    assert main(["ai-review", str(path), "--format", "json", "--fail-on", "none"]) == 0

    stdout.flush()
    decoded = raw.getvalue().decode("cp1251")
    assert "\\u00fc" in decoded
    assert "\\ud83d\\ude00" in decoded
    payload = json.loads(decoded)
    assert payload["improved_spec"] == "# Goal\n\nExport orders for M\u00fcnchen \U0001f600 users."


def test_check_json_survives_cp1251_stdout(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    path = tmp_path / "m\u00f6d-task.md"
    path.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")

    raw = io.BytesIO()
    stdout = io.TextIOWrapper(raw, encoding="cp1251", newline="\n")
    monkeypatch.setattr(sys, "stdout", stdout)

    assert main(["check", str(path), "--format", "json", "--fail-on", "none"]) == 0

    stdout.flush()
    decoded = raw.getvalue().decode("cp1251")
    assert "\\u00f6" in decoded
    payload = json.loads(decoded)
    assert payload["source"] == str(path)


def test_ai_review_requires_explicit_environment_provider(
    tmp_path: Path,
    monkeypatch: object,
    capsys: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text(_specification(), encoding="utf-8")
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: None,
    )

    assert main(["ai-review", str(path), "--fail-on", "none"]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "AI provider is not configured" in captured.err
    assert "Traceback" not in captured.err


def test_ai_review_preserves_deterministic_fail_on_semantics(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")
    provider = SequenceProvider(
        [
            '{"contradictions":[]}',
            "# Goal\n\nTODO: clarify the requested behavior.",
        ]
    )
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: provider,
    )

    assert main(["ai-review", str(path)]) == 1


def test_ai_review_text_and_markdown_are_human_reviewable(
    tmp_path: Path,
    monkeypatch: object,
    capsys: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text(_specification(), encoding="utf-8")

    text_provider = _provider()
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: text_provider,
    )
    assert main(["ai-review", str(path), "--fail-on", "none"]) == 0
    text_output = capsys.readouterr().out
    assert "AI REVIEW" in text_output
    assert "Provider: fake" in text_output
    assert "Contradictions: 1" in text_output
    assert "Draft gate:" in text_output
    assert "Draft findings:" in text_output
    assert "IMPROVED SPECIFICATION" in text_output

    markdown_provider = _provider()
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: markdown_provider,
    )
    assert (
        main(
            [
                "ai-review",
                str(path),
                "--format",
                "markdown",
                "--fail-on",
                "none",
            ]
        )
        == 0
    )
    markdown_output = capsys.readouterr().out
    assert "# SpecForge Gate AI Review" in markdown_output
    assert "## Draft deterministic report" in markdown_output
    assert "## Contradictions" in markdown_output
    assert "## Improved specification" in markdown_output


def test_ai_review_text_escapes_terminal_control_characters(
    tmp_path: Path,
    monkeypatch: object,
    capsys: object,
) -> None:
    path = tmp_path / "task.md"
    path.write_text(_specification(), encoding="utf-8")
    provider = SequenceProvider(
        [
            '{"contradictions":[]}',
            "# Goal\n\x1b[31mDo not emit terminal control sequences.",
        ]
    )
    monkeypatch.setattr(
        "specforge_gate.ai.runtime.provider_from_environment",
        lambda: provider,
    )

    assert main(["ai-review", str(path), "--fail-on", "none"]) == 0

    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert "\\u001b" in output
