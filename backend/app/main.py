"""Sonics backend application entry point.

This module defines the FastAPI application and the ``sonics`` CLI entry
point.  Dependencies are installed once at setup time (``pip install .``);
nothing here triggers a package install at runtime.  User-supplied usernames
are treated purely as data.

Running ``sonics`` starts the API **and** serves the pre-built dashboard from
``app/static`` (embedded in the installed package), so a single command gives
a complete working application. The CLI prints a startup banner with the
dashboard URL and active AI provider, checks that the configured port is free,
warns (non-fatally) if Ollama is unreachable or its model is missing, and
auto-opens the dashboard in a browser (disable with ``SONICS_NO_BROWSER=1``).
"""
from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .agents.providers.ollama import DEFAULT_MODEL
from .api.routes import router

logger = logging.getLogger("sonics")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _load_env() -> None:
    """Load .env from the current directory and from the backend folder."""
    load_dotenv(Path.cwd() / ".env")
    backend_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(backend_env)


_load_env()

app = FastAPI(
    title="Sonics — Instagram AI Policy & Evidence Analyzer",
    description=(
        "Read-only Instagram profile/content analysis producing evidence-confidence "
        "policy assessments. Does not submit reports, ban accounts, or predict "
        "enforcement outcomes."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve the pre-built dashboard (the React app is built into
# backend/app/static and ships inside the pip package).
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="dashboard")
    logger.info("Dashboard available at http://127.0.0.1:%s (serving %s)",
                os.getenv("SONICS_PORT", os.getenv("PORT", "8000")), STATIC_DIR)
else:
    logger.warning(
        "Frontend build not found at %s — running API-only. "
        "Build it with: cd frontend && npm install && npm run build",
        STATIC_DIR,
    )


def _port_in_use(host: str, port: int) -> bool:
    """Return True if something is already listening on host:port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
        return False
    except OSError:
        return True


def _check_ollama() -> tuple[Optional[str], str]:
    """Return (warning, model) for the configured Ollama setup.

    Never blocks startup: if Ollama is unreachable the app can still run in
    deterministic fallback mode, so this is a warning-only health check.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
    except Exception as exc:
        return (
            f"Could not reach Ollama at {base_url} ({exc.__class__.__name__}). "
            "Start the Ollama app and re-run. Until then, the backend will use "
            "the deterministic fallback engine.",
            model,
        )
    if response.status_code != 200:
        return (
            f"Ollama at {base_url} answered HTTP {response.status_code}. "
            "The backend will use the deterministic fallback engine.",
            model,
        )
    installed = [tag.get("name", "") for tag in response.json().get("models", [])]
    if model not in installed:
        return (
            f"Ollama is running but model '{model}' is not installed yet. "
            f"Install it once with:  ollama pull {model}",
            model,
        )
    return (None, model)


def _open_browser_delayed(url: str) -> None:
    """Open the dashboard in a browser shortly after the server starts."""

    def _open() -> None:
        time.sleep(1.8)
        try:
            webbrowser.open(url)
        except Exception:  # best effort — never crash the CLI for this
            logger.debug("Could not auto-open the browser.", exc_info=True)

    threading.Thread(target=_open, daemon=True).start()


def main() -> int:
    """Start the Sonics backend using the configured host/port."""
    host = os.getenv("SONICS_HOST", os.getenv("HOST", "127.0.0.1"))
    port = int(os.getenv("SONICS_PORT", os.getenv("PORT", "8000")))
    url = f"http://{host}:{port}"

    if _port_in_use(host, port):
        print(f"✖ Port {host}:{port} is already in use.")
        print("  - Another Sonics instance may already be running, or")
        print(f"  - Another program is using it. Set PORT={port + 1} in your .env and retry.")
        return 1

    provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
    model = ""
    warnings: list[str] = []
    if provider == "ollama":
        warning, model = _check_ollama()
        if warning:
            warnings.append(warning)

    line = "=" * 62
    print(line)
    print("  Sonics — Instagram AI Policy & Evidence Analyzer")
    print("  Read-only analysis of publicly accessible Instagram data.")
    print(line)
    print(f"  Dashboard:   {url}")
    if provider == "ollama" and model:
        print(f"  AI provider: {provider}  |  model: {model}")
    else:
        print(f"  AI provider: {provider}")
    print(line)
    if warnings:
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print("  Status: OK   (Ctrl+C to stop the server)")
    print(line)

    if os.getenv("SONICS_NO_BROWSER", "0") != "1" and os.getenv("CI", "").lower() != "true":
        _open_browser_delayed(url)

    uvicorn.run("app.main:app", host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())