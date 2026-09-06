"""Tests for the Ollama AI provider (httpx MockTransport, no network)."""
import json

import httpx
import pytest

from app.agents.providers.ollama import (
    OllamaAIProvider,
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
)


def _make_provider(handler):
    return OllamaAIProvider(
        base_url="http://unit.test:11434",
        model="unit-model",
        transport=httpx.MockTransport(handler),
    )


def _json_ok(content):
    def handler(request):
        body = json.loads(request.content)
        assert body["model"] == "unit-model"
        assert body.get("format") == "json"
        assert body.get("stream") is False
        assert body["messages"][0]["role"] == "system"
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"message": {"content": content}})
    return handler


def test_generate_json_success():
    provider = _make_provider(_json_ok('{"ok": true, "value": 42}'))
    result = provider.generate_json(system="s", user="u")
    assert result == {"ok": True, "value": 42}


def test_generate_json_strips_markdown_fences():
    provider = _make_provider(_json_ok('```json\n{"status": "ok"}\n```'))
    assert provider.generate_json(system="s", user="u") == {"status": "ok"}


def test_generate_json_extracts_object_from_prose():
    provider = _make_provider(_json_ok('Here you go: {"category": "Spam"}. Done'))
    assert provider.generate_json(system="s", user="u") == {"category": "Spam"}


def test_malformed_json_raises():
    provider = _make_provider(_json_ok("sorry, not json at all"))
    with pytest.raises(OllamaResponseError):
        provider.generate_json(system="s", user="u")


def test_empty_response_raises():
    provider = _make_provider(_json_ok("   "))
    with pytest.raises(OllamaResponseError):
        provider.generate_json(system="s", user="u")


def test_model_not_found_raises():
    def handler(request):
        return httpx.Response(404, text="model 'unit-model' not found")
    provider = _make_provider(handler)
    with pytest.raises(OllamaModelNotFoundError):
        provider.generate_json(system="s", user="u")


def test_connection_error_raises():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)
    provider = _make_provider(handler)
    with pytest.raises(OllamaConnectionError):
        provider.generate_json(system="s", user="u")


def test_timeout_raises():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)
    provider = _make_provider(handler)
    with pytest.raises(OllamaTimeoutError):
        provider.generate_json(system="s", user="u")


def test_server_error_raises():
    def handler(request):
        return httpx.Response(500, text="internal error")
    provider = _make_provider(handler)
    with pytest.raises(OllamaError):
        provider.generate_json(system="s", user="u")


def test_list_root_json_wrapped_in_object_succeeds():
    # A top-level list containing an object is tolerated by extracting that
    # object (models sometimes wrap their answer in an array).
    provider = _make_provider(_json_ok('[{"status": "ok"}]'))
    assert provider.generate_json(system="s", user="u") == {"status": "ok"}


def test_no_prompt_raises():
    provider = _make_provider(lambda r: httpx.Response(200))
    with pytest.raises(ValueError):
        provider.generate_json()
