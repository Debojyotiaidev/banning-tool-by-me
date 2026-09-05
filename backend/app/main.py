"""Sonics backend application entry point.

This module defines the FastAPI application and the ``sonics`` CLI entry
point.  Dependencies are installed once at setup time (``pip install .``);
nothing here triggers a package install at runtime.  User-supplied usernames
are treated purely as data.
"""
from __future__ import annotations

import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

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


def main() -> int:
    """Start the Sonics backend using the configured host/port."""
    host = os.getenv("SONICS_HOST", "127.0.0.1")
    port = int(os.getenv("SONICS_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())