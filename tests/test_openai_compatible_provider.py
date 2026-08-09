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
    OpenAICompatibleProvider,
)
from specforge_gate.ai import openai_compatible as openai_module


class FakeHTTPResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        return self._body


def _response(*, content: str = "answer", model: str = "gpt-test") -> bytes:
    return json.dumps(
        {
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        }
    ).encode("utf-8")


def _provider(**overrides: object) -> OpenAICompatibleProvider:
    kwargs: dict[str, object] = {
        "model": "gpt-test",
        "base_url": "https://api.example.test/v1",
    }
    kwargs.update(overrides)
    return OpenAICompatibleProvider(**kwargs)  # type: ignore[arg-type]


def test_provider_is_structural_and_normalizes_configuration() -> None:
    provider = OpenAICompatibleProvider(
        model=" gpt-test ",
        base_url=" https://api.example.test/v1/ ",
    )

    assert isinstance(provider, AIProvider)
    assert provider.provider_id == "openai-compatible"
    assert provider.model == "gpt-test"
    assert provider.base_url == "https://api.example.test/v1"
    assert provider.timeout == 60.0


def test_generate_posts_chat_completions_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: object, timeout: float) -> FakeHTTPResponse:
        captured["request"] = http_request
        captured["timeout"] = timeout
        return FakeHTTPResponse(_response())

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    provider = _provider(api_key=" test-secret ", timeout=15.5)

    result = provider.generate(AIRequest("System prompt", "User prompt"))

    request = captured["request"]
    assert isinstance(request, openai_module.urlrequest.Request)
    assert request.full_url == "https://api.example.test/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("Authorization") == "Bearer test-secret"
    assert captured["timeout"] == 15.5
    assert json.loads(request.data.decode("utf-8")) == {
        "model": "gpt-test",
        "messages": [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User prompt"},
        ],
        "stream": False,
    }
    assert result == AIResponse(text="answer", provider="openai-compatible", model="gpt-test")


def test_api_key_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        captured["request"] = http_request
        return FakeHTTPResponse(_response())

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    _provider(base_url="http://127.0.0.1:1234/v1").generate(AIRequest("system", "user"))

    request = captured["request"]
    assert isinstance(request, openai_module.urlrequest.Request)
    assert request.get_header("Authorization") is None


def test_json_mode_maps_to_json_object(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        assert isinstance(http_request, openai_module.urlrequest.Request)
        captured.update(json.loads(http_request.data.decode("utf-8")))
        return FakeHTTPResponse(_response(content='{"items":[]}'))

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    result = _provider().generate(
        AIRequest("Return JSON.", "Find contradictions.", AIResponseFormat.JSON)
    )

    assert captured["response_format"] == {"type": "json_object"}
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
            url="https://api.example.test/v1/chat/completions",
            code=status,
            msg="failure",
            hdrs=Message(),
            fp=None,
        )

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is expected_code
    assert raised.value.provider == "openai-compatible"
    assert raised.value.retryable is retryable


def test_timeout_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise TimeoutError("slow")

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.TIMEOUT
    assert raised.value.retryable is True


def test_url_error_timeout_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise error.URLError(TimeoutError("slow"))

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.TIMEOUT


def test_url_error_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise error.URLError("connection refused")

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fake_urlopen)
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.UNAVAILABLE
    assert raised.value.retryable is True


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"[]",
        b'{"model":"gpt-test"}',
        b'{"model":"gpt-test","choices":[]}',
        b'{"model":"gpt-test","choices":[123]}',
        b'{"model":"gpt-test","choices":[{}]}',
        b'{"model":"gpt-test","choices":[{"message":{"content":123}}]}',
        b'{"model":"","choices":[{"message":{"content":"answer"}}]}',
    ],
)
def test_invalid_responses_are_normalized(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
) -> None:
    monkeypatch.setattr(
        openai_module.urlrequest,
        "urlopen",
        lambda _request, timeout: FakeHTTPResponse(body),
    )
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.INVALID_RESPONSE
    assert raised.value.retryable is False


def test_oversized_response_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    oversized = b"x" * (openai_module._MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(
        openai_module.urlrequest,
        "urlopen",
        lambda _request, timeout: FakeHTTPResponse(oversized),
    )
    with pytest.raises(AIProviderError) as raised:
        _provider().generate(AIRequest("system", "user"))

    assert raised.value.code is AIProviderErrorCode.INVALID_RESPONSE


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"model": "   ", "base_url": "https://api.example.test/v1"}, "model"),
        ({"timeout": 0}, "timeout"),
        ({"timeout": float("nan")}, "timeout"),
        ({"base_url": "ftp://localhost/v1"}, "base_url"),
        ({"base_url": "http://user:pass@localhost/v1"}, "base_url"),
        ({"base_url": "http://localhost/v1?x=1"}, "base_url"),
        ({"base_url": "http://localhost/v1#fragment"}, "base_url"),
        ({"base_url": "http://localhost:bad/v1"}, "base_url"),
        ({"api_key": "  "}, "api_key"),
        ({"api_key": "a\nb"}, "api_key"),
    ],
)
def test_invalid_configuration_is_rejected(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(AIProviderError, match=message) as raised:
        _provider(**kwargs)

    assert raised.value.code is AIProviderErrorCode.CONFIGURATION
    assert raised.value.provider == "openai-compatible"
    assert raised.value.retryable is False


def test_construction_does_not_call_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(_request: object, timeout: float) -> FakeHTTPResponse:
        del timeout
        raise AssertionError("construction must not call network")

    monkeypatch.setattr(openai_module.urlrequest, "urlopen", fail_urlopen)
    provider = _provider(api_key="secret")

    assert provider.model == "gpt-test"
