"""Ollama AI provider.

Talks to a local Ollama server through its HTTP API using the existing
``httpx`` dependency. No paid API keys and no third-party Ollama SDK are
required.

The provider requests structured JSON output and raises specific
``OllamaError`` subclasses for connection, timeout, missing-model, and
malformed-output failures so callers can degrade gracefully instead of
crashing the analysis pipeline.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

import httpx


class OllamaError(Exception):
    """Base class for all Ollama provider failures."""


class OllamaConnectionError(OllamaError):
    """Cannot reach the Ollama server."""


class OllamaTimeoutError(OllamaError):
    """The Ollama server did not answer in time."""


class OllamaModelNotFoundError(OllamaError):
    """The requested model is not installed on the Ollama server."""


class OllamaResponseError(OllamaError):
    """The Ollama server returned an unusable (empty / malformed) response."""


DEFAULT_BASE_URL = "http://127.0.0.1:11434"
# Default model is intentionally lightweight so the app runs comfortably on
# typical 8 GB RAM machines. Override via OLLAMA_MODEL in .env if you want a
# larger model (e.g. llama3.1:8b on machines with 16 GB+ RAM).
DEFAULT_MODEL = "llama3.2:3b"


class OllamaAIProvider:
    """Minimal HTTP client for Ollama's /api/chat endpoint."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.timeout = (
            timeout if timeout is not None else float(os.getenv("OLLAMA_TIMEOUT", "120"))
        )
        self._client = httpx.Client(
            base_url=self.base_url, timeout=self.timeout, transport=transport
        )

    def close(self) -> None:
        self._client.close()

    @property
    def available(self) -> bool:
        """Cheap health probe for callers that want to pre-check Ollama."""
        try:
            response = self._client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def generate_json(
        self,
        system: Optional[str] = None,
        user: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Send a chat request and return the parsed JSON reply.

        Raises:
            OllamaConnectionError -- server unreachable.
            OllamaTimeoutError -- server did not respond in time.
            OllamaModelNotFoundError -- the configured model is not installed.
            OllamaResponseError -- empty or malformed model output.
            OllamaError -- any other HTTP-level failure.
        """
        if not (system or user):
            raise ValueError("A system or user prompt is required.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if user:
            messages.append({"role": "user", "content": user})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            response = self._client.post("/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                f"Ollama request timed out after {self.timeout:.0f}s at {self.base_url}."
            ) from exc
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is the Ollama server running?"
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama HTTP request failed: {exc}") from exc

        self._raise_for_status(response)

        try:
            data = response.json()
        except ValueError as exc:
            raise OllamaResponseError(
                f"Ollama returned a non-JSON HTTP response body: {response.text[:200]!r}"
            ) from exc

        text = ((data.get("message") or {}).get("content")) or data.get("response") or ""
        if not (text or "").strip():
            raise OllamaResponseError("Ollama returned an empty model response.")

        return self._parse_json(text)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 200:
            return
        body = (response.text or "")[:300]
        if response.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{self.model}' not found on Ollama (HTTP 404): {body}"
            )
        raise OllamaError(f"Ollama returned HTTP {response.status_code}: {body}")

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        cleaned = (text or "").strip()
        # Strip markdown code fences that some models add around JSON.
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned).strip()
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        # Tolerate prose wrapped around a single JSON object.
        for opener, closer in (("{", "}"), ("[", "]")):
            start = cleaned.find(opener)
            end = cleaned.rfind(closer)
            if start != -1 and end > start:
                try:
                    data = json.loads(cleaned[start : end + 1])
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    continue
        raise OllamaResponseError(f"Malformed JSON from Ollama: {cleaned[:200]!r}")