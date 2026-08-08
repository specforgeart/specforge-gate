from __future__ import annotations

import json
from email.message import Message
from urllib import error

import pytest

from specforge_gate.ai import (
    AIProvider,
    AIProviderError,
    AIProviderErrorCode,
    AIRequest,
    AIResponse,
    AIResponseFormat,
    OllamaProvider,
)
from specforge_gate.ai import ollama as ollama_module


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._body


def _response(*, content: str = "answer", model: str = "qwen3:8b") -> bytes:
    return json.dumps(
        {
            "model": model,
            "message": {"role": "assistant", "content": content},
            "done": True,
        }
    ).encode("utf-8")


def test_ollama_provider_is_structural_provider() -> None:
    provider = OllamaProvider(model=" qwen3:8b ")

    assert isinstance(provider, AIProvider)
    assert provider.provider_id == "ollama"
    assert provider.model == "qwen3:8b"
    assert provider.base_url == "http://127.0.0.1:11434"
    assert provider.timeout == 60.0


def test_generate_posts_non_streaming_chat_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: object, timeout: float) -> FakeHTTPResponse:
        captured["request"] = http_request
        captured["timeout"] = timeout
        return FakeHTTPResponse(_response())

    monkeypatch.setattr(ollama_module.urlrequest, "urlopen", fake_urlopen)
    provider = OllamaProvider(model="qwen3:8b", timeout=12.5)

    result = provider.generate(AIRequest("System prompt", "User prompt"))

    http_request = captured["request"]
    assert isinstance(http_request, ollama_module.urlrequest.Request)
    assert http_request.full_url == "http://127.0.0.1:11434/api/chat"
    assert http_request.get_method() == "POST"
    assert http_request.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 12.5
    assert json.loads(http_request.data.decode("utf-8")) == {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User prompt"},
        ],
        "stream": False,
    }
    assert result == AIResponse(text="answer", provider="ollama", model="qwen3:8b")


def test_json_mode_maps_to_ollama_format_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload: dict[str, object] = {}

    def fake_urlopen(http_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        assert isinstance(http_request, ollama_module.urlrequest.Request)
        captured_payload.update(json.loads(http_request.data.decode("utf-8")))
        return FakeHTTPResponse(_response(content='{"items":[]}'))

    monkeypatch.setattr(ollama_module.urlrequest, "urlopen", fake_urlopen)

    result = OllamaProvider(model="qwen3:8b").generate(
        AIRequest("Return JSON.", "Find contradictions.", AIResponseFormat.JSON)
    )

    assert captured_payload["format"] == "json"
    assert result.text == '{"items":[]}'


@pytest.mark.parametrize(
    ("status", "expected_code", "retryable"),
    [
        (400, AIProviderErrorCode.REQUEST_REJECTED, False),
        (401, AIProviderErrorCode.AUTHENTICATION, False),
        (403, AIProviderErrorCode.AUTHENTICATION, False),
        (404, AIProviderErrorCode.REQUEST_REJECTED, False),
        (408, AIProviderErrorCode.TIMEOUT, True),
        (429, AIProviderErrorCode.RATE_LIMITED, True),
        (500, AIProviderErrorCode.UNAVAILABLE, True),
        (503, AIProviderErrorCode.UNAVAILABLE, True),
    ],
)
def test_http_errors_are_normalized(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    expected_code: AIProviderErrorCode,
    retryable: bool,
) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise error.HTTPError(
            url="http://127.0.0.1:11434/api/chat",
            code=status,
            msg="failure",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr(ollama_module.urlrequest, "urlopen", fake_urlopen)

    with pytest.raises(AIProviderError) as raised:
        OllamaProvider(model="qwen3:8b").generate(AIRequest("system", "user"))

    assert raised.value.code is expected_code
    assert raised.value.provider == "ollama"
    assert raised.value.retryable is retryable


def test_socket_timeout_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise TimeoutError("slow")

    monkeypatch.setattr(ollama_module.urlrequest, "urlopen", fake_urlopen)

    with pytest.raises(AIProviderError) as raised:
        OllamaProvider(model="qwen3:8b").generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.TIMEOUT
    assert raised.value.retryable is True


def test_url_error_is_normalized_as_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise error.URLError("connection refused")

    monkeypatch.setattr(ollama_module.urlrequest, "urlopen", fake_urlopen)

    with pytest.raises(AIProviderError) as raised:
        OllamaProvider(model="qwen3:8b").generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.UNAVAILABLE
    assert raised.value.retryable is True


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"[]",
        b'{"model":"qwen3:8b"}',
        b'{"model":"qwen3:8b","message":{"content":123}}',
        b'{"model":"","message":{"content":"answer"}}',
    ],
)
def test_invalid_responses_are_normalized(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
) -> None:
    monkeypatch.setattr(
        ollama_module.urlrequest,
        "urlopen",
        lambda _request, timeout: FakeHTTPResponse(body),
    )

    with pytest.raises(AIProviderError) as raised:
        OllamaProvider(model="qwen3:8b").generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.INVALID_RESPONSE
    assert raised.value.retryable is False


def test_oversized_response_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    oversized = b"x" * (ollama_module._MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(
        ollama_module.urlrequest,
        "urlopen",
        lambda _request, timeout: FakeHTTPResponse(oversized),
    )

    with pytest.raises(AIProviderError) as raised:
        OllamaProvider(model="qwen3:8b").generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.INVALID_RESPONSE


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"model": "   "}, "model"),
        ({"model": "qwen3:8b", "timeout": 0}, "timeout"),
        ({"model": "qwen3:8b", "timeout": float("nan")}, "timeout"),
        ({"model": "qwen3:8b", "base_url": "ftp://localhost"}, "base_url"),
        ({"model": "qwen3:8b", "base_url": "http://user:pass@localhost:11434"}, "base_url"),
        ({"model": "qwen3:8b", "base_url": "http://localhost:11434/api"}, "base_url"),
    ],
)
def test_invalid_configuration_is_rejected(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(AIProviderError, match=message) as raised:
        OllamaProvider(**kwargs)  # type: ignore[arg-type]

    assert raised.value.code is AIProviderErrorCode.CONFIGURATION
    assert raised.value.provider == "ollama"
    assert raised.value.retryable is False


def test_base_url_is_normalized_without_network_call() -> None:
    provider = OllamaProvider(
        model="qwen3:8b",
        base_url=" https://ollama.internal.example:11434/ ",
    )

    assert provider.base_url == "https://ollama.internal.example:11434"
