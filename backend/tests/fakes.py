"""Shared test helpers for the Sonics backend test suite."""
from app.models.schemas import InstagramProfile


class FakeProvider:
    """Deterministic mock provider for pipeline tests."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_json(self, system=None, user=None, temperature=0.2, max_tokens=2048):
        self.calls.append({"system": system, "user": user})
        if not self.responses:
            raise AssertionError("FakeProvider exhausted: unexpected extra LLM call.")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def make_public_profile():
    return InstagramProfile(
        username="demo_account",
        display_name="Demo Account",
        bio="DM for promo. Buy followers, link in bio!!!",
        profile_pic_url="Unavailable",
        is_private=False,
        follower_count=1200,
        following_count=100,
        post_count=3,
        recent_posts=[
            {"caption": "get free followers now, click the link", "url": "https://example.invalid/a", "timestamp": "2024-01-01T10:00:00"},
            {"caption": "just a photo of my dog #doggo", "url": "https://example.invalid/b", "timestamp": "2024-01-02T10:00:00"},
            {"caption": "best prices for followers DM me", "url": "https://example.invalid/c", "timestamp": "2024-01-03T10:00:00"},
        ],
        access_status="Public",
    )


def make_private_profile():
    return InstagramProfile(
        username="private_user",
        display_name="Private User",
        bio="Small business. Buy followers, link in bio.",
        profile_pic_url="Unavailable",
        is_private=True,
        follower_count=50,
        following_count=0,
        post_count=10,
        recent_posts=[],
        access_status="Private",
    )


def make_not_found_profile():
    return InstagramProfile(
        username="ghost",
        display_name="Unavailable",
        bio="Unavailable",
        profile_pic_url="Unavailable",
        is_private=False,
        follower_count=None,
        following_count=None,
        post_count=None,
        recent_posts=[],
        access_status="Account not found",
    )


# Canonical LLM responses for the full four-step path.
CONTENT_RESPONSE = {
    "observations": [
        {"reference": "bio", "quote": "Buy followers, link in bio", "text": "Bio promotes buying followers and directs to an external link.", "content_signal": "commercial promotion", "context_clue": "promotional bio", "confidence": 0.9},
        {"reference": "post#1", "quote": "get free followers now", "text": "Caption promotes free follower growth.", "content_signal": "promotion", "context_clue": "engagement bait", "confidence": 0.85},
        {"reference": "post#3", "quote": "best prices for followers", "text": "Caption advertises paid follower services.", "content_signal": "promotion", "context_clue": "sales pitch", "confidence": 0.8},
        {"reference": "post#2", "quote": "this quote is invented and does not exist", "text": "fabricated", "content_signal": "", "context_clue": "", "confidence": 0.9},
    ]
}

CONTEXT_RESPONSE = {
    "discourse_modes": [
        {"mode": "promotion", "detail": "Captions promote follower services.", "confidence": 0.85},
        {"mode": "imaginary", "detail": "invalid mode", "confidence": 0.9},
    ]
}

POLICY_RESPONSE = {
    "candidates": [
        {"category": "Fraud / Scams / Deceptive Practices", "relevant": True, "rationale": "Repeated offers to sell followers.", "evidence_refs": ["bio", "post#1", "post#3"], "initial_confidence": 0.8},
        {"category": "Spam", "relevant": True, "rationale": "Repetitive promotional captions.", "evidence_refs": ["bio", "post#1"], "initial_confidence": 0.62},
        {"category": "Dangerous Organizations & Individuals", "relevant": False, "rationale": "No evidence.", "evidence_refs": [], "initial_confidence": 0.05},
        {"category": "Not A Real Category", "relevant": True, "rationale": "x", "evidence_refs": ["bio"], "initial_confidence": 0.9},
    ]
}

VERIFIER_RESPONSE = {
    "findings": [
        {"category": "Fraud / Scams / Deceptive Practices", "accepted": True, "confidence_adjustment": 0.05, "rejection_reason": None},
        {"category": "Spam", "accepted": True, "confidence_adjustment": -0.1, "rejection_reason": None},
    ]
}


def all_content(profile):
    parts = []
    if profile.bio:
        parts.append(profile.bio)
    for p in profile.recent_posts or []:
        if p.get("caption"):
            parts.append(p["caption"])
    return "\n".join(parts)
