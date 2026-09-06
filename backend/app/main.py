"""Sonics backend application entry point.

This module defines the FastAPI application and the ``sonics`` CLI entry
point.  Dependencies are installed once at setup time (``pip install .``);
nothing here triggers a package install at runtime.  User-supplied usernames
are treated purely as data.

Running ``sonics`` starts the API **and** serves the pre-built dashboard from
``app/static`` (embedded in the installed package), so a single command gives
a complete working application.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    title="Sonics — Instagram AI Account Analyzer & Enforcement Prediction Simulator",
    description=(
        "Read-only Instagram profile/content analysis with a hypothetical "
        "enforcement prediction simulator. Does not submit reports or affect "
        "Instagram enforcement."
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


def main() -> int:
    """Start the Sonics backend using the configured host/port."""
    host = os.getenv("SONICS_HOST", os.getenv("HOST", "127.0.0.1"))
    port = int(os.getenv("SONICS_PORT", os.getenv("PORT", "8000")))
    uvicorn.run("app.main:app", host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())