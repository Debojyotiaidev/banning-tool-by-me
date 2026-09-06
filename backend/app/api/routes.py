"""API routes for the Sonics backend."""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.analyzer import AnalysisPipeline
from ..instagram.client import InstagramClient
from ..models.schemas import InstagramProfile
from ..simulation.schemas import AccountRisk, SimulationInput, SimulationOutput
from ..simulation.simulator import SonicsSimulator

router = APIRouter(prefix="/api")

USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def _extract_username(value: str) -> str:
    """Extract a username from a raw value (with or without @ / URL)."""
    raw = (value or "").strip()
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", raw)
    if match:
        return match.group(1)
    return raw.lstrip("@").strip()


class AnalyzeRequest(BaseModel):
    username: str


class SimulateRequest(BaseModel):
    risk: AccountRisk
    inputs: SimulationInput


def _empty_profile(username: str, status: str) -> InstagramProfile:
    return InstagramProfile(
        username=username,
        display_name="Unavailable",
        bio="Unavailable",
        profile_pic_url="Unavailable",
        is_private=False,
        follower_count=None,
        following_count=None,
        post_count=None,
        recent_posts=[],
        access_status=status,
    )


@router.get("")
def read_root() -> dict:
    return {"message": "Banning Tool API is running"}


@router.post("/analyze")
def analyze(body: AnalyzeRequest) -> dict:
    username = _extract_username(body.username)
    if not USERNAME_RE.match(username):
        raise HTTPException(status_code=400, detail="Invalid Instagram username.")

    client = InstagramClient()
    profile = client.get_profile(username)

    if profile is None:
        profile = _empty_profile(username, "Account not found")
    elif profile.recent_posts is None:
        profile.recent_posts = []

    # Read-only evidence-confidence policy assessment.
    # This endpoint deliberately does NOT produce ban/enforcement probabilities.
    pipeline = AnalysisPipeline()
    analysis = pipeline.run(profile)

    return {
        "profile": profile,
        "access_status": profile.access_status if profile.access_status else "Unavailable",
        "analysis": analysis,
    }


@router.post("/simulate")
def simulate(body: SimulateRequest) -> SimulationOutput:
    simulator = SonicsSimulator()
    return simulator.calculate_likelihood(body.risk, body.inputs)