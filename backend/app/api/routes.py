"""API routes for the Sonics backend."""
from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..instagram.client import InstagramClient
from ..agents.analyzer import AnalysisAgent, AccountLevelAgent
from ..simulation.simulator import SonicsSimulator
from ..models.schemas import (
    AccountRisk,
    AnalysisResult,
    InstagramProfile,
    SimulationInput,
    SimulationOutput,
)

router = APIRouter(prefix="/api")

CATEGORIES = [
    "Spam",
    "Harassment / Bullying",
    "Hate Speech",
    "Impersonation Risk",
    "General Policy Risk",
]

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

    # Build the content capture for analysis (actual retrieved data only).
    content_parts = []
    if profile.bio and profile.bio != "Unavailable":
        content_parts.append(f"Bio: {profile.bio}")
    for post in profile.recent_posts:
        caption = (post.get("caption") or "").strip()
        if caption:
            content_parts.append(f"Post: {caption}")
    content_data = "\n".join(content_parts)

    analysis_agent = AnalysisAgent()
    content_analysis: list = []
    for category in CATEGORIES:
        try:
            result = analysis_agent.analyze_content(content_data, category)
            content_analysis.append(result)
        except Exception:
            content_analysis.append(
                AnalysisResult(
                    category=category,
                    classification="Unavailable",
                    confidence=0.0,
                    severity="Unavailable",
                    evidence="Unavailable",
                    explanation="Analysis failed — data unavailable.",
                )
            )

    account_agent = AccountLevelAgent()
    try:
        account_risk_data = account_agent.aggregate_analysis(profile, content_analysis)
        account_risk = AccountRisk(**account_risk_data)
    except Exception:
        account_risk = AccountRisk(
            overall_score=0.0,
            detected_categories=[],
            severity="Unavailable",
            confidence=0.0,
            items_analyzed=len(profile.recent_posts),
            summary="Data unavailable — account-level analysis failed.",
        )

    simulator = SonicsSimulator()
    simulation = simulator.calculate_likelihood(account_risk, SimulationInput())

    return {
        "profile": profile,
        "access_status": profile.access_status
        if profile.access_status
        else "Unavailable",
        "content_analysis": content_analysis,
        "account_risk": account_risk,
        "enforcement_simulation": simulation,
    }


@router.post("/simulate")
def simulate(body: SimulateRequest) -> SimulationOutput:
    simulator = SonicsSimulator()
    return simulator.calculate_likelihood(body.risk, body.inputs)