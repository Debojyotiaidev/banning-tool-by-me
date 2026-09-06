"""Context / Behavior Analyst role.

Analyzes observable context: public account metrics, posting patterns,
repeated themes, and discourse modes. Never infers sensitive personal
characteristics. A private account is never treated as suspicious.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import List, Optional, Tuple

from ..models.schemas import (
    ContentAnalysis, ContextAnalysis, ContextSignal, DiscourseMode, InstagramProfile,
)
from .content_analyst import collect_content_items

DISCOURSE_MODES = [
    "discussion", "education", "news/reporting", "criticism", "condemnation",
    "quotation", "satire", "support", "promotion", "glorification",
    "threats", "instructions",
]

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on",
    "for", "with", "at", "from", "by", "is", "are", "was", "were", "it",
    "this", "that", "you", "your", "yourself", "we", "our", "us", "they",
    "them", "their", "my", "me", "be", "as", "no", "not", "do", "just",
    "get", "now", "via", "im", "dont", "cant", "please", "also",
}


class ContextBehaviorAnalyst:
    """Context signals + LLM-assisted discourse-mode classification."""

    SYSTEM_PROMPT = (
        "You are the Context / Behavior Analyst component of 'Sonics', a "
        "read-only Instagram policy and evidence analysis tool.\n"
        "Analyze the publicly accessible context supplied and identify the "
        "dominant discourse modes.\n"
        "Allowed discourse modes: "
        + ", ".join(f"'{m}'" for m in DISCOURSE_MODES)
        + ".\n"
        "Rules:\n"
        "- Only report a mode when the supplied content clearly supports it.\n"
        "- Quoting, reporting on, criticizing, or condemning a topic is NOT "
        "the same as promoting or glorifying it.\n"
        "- Never infer sensitive personal characteristics about the account owner.\n"
        "- A private account is never, by itself, suspicious.\n"
        "Return ONLY JSON:\n"
        '{"discourse_modes": [{"mode": "...", "detail": "...", "confidence": 0.0}]}'
    )

    def __init__(self, provider: object) -> None:
        self.provider = provider

    def analyze(self, profile, content):
        signals = self.metrics(profile, content)
        modes = []
        if content.observations and hasattr(self.provider, "generate_json"):
            user_prompt = self._build_user_prompt(profile, content)
            data = self.provider.generate_json(
                system=self.SYSTEM_PROMPT, user=user_prompt,
                temperature=0.1, max_tokens=800,
            )
            modes = self._parse_discourse(data)
        if not signals and not modes:
            return ContextAnalysis(status="unavailable", note="No context signals derived.")
        return ContextAnalysis(discourse_modes=modes, signals=signals, status="completed")

    def metrics(self, profile, content):
        """Deterministic public-metric signals (also used by fallback)."""
        signals = []
        followers = profile.follower_count
        following = profile.following_count
        if followers is not None and followers > 0 and following:
            ratio = followers / max(1, following)
            signals.append(ContextSignal(
                trait="follower_to_following_ratio",
                description=f"~{ratio:.2f} followers per following account",
                reference="profile_metadata", confidence=0.6,
            ))
        if profile.post_count is not None:
            signals.append(ContextSignal(
                trait="post_count",
                description=f"{profile.post_count} total public posts",
                reference="profile_metadata", confidence=0.5,
            ))
        if profile.bio and "http" in profile.bio.lower():
            signals.append(ContextSignal(
                trait="bio_contains_link",
                description="bio contains an external link",
                reference="bio", confidence=0.7,
            ))
        items = collect_content_items(profile)
        timestamps = [ts for _r, _t, ts in items if ts]
        parsed = []
        for ts in timestamps:
            try:
                parsed.append(datetime.fromisoformat(str(ts).replace("Z", "+00:00")))
            except (TypeError, ValueError):
                continue
        if len(parsed) >= 2:
            parsed.sort()
            days = (parsed[-1] - parsed[0]).total_seconds() / 86400.0
            span = max(days, 0.01)
            signals.append(ContextSignal(
                trait="posting_frequency",
                description=f"{len(parsed)} recent posts across ~{span:.1f} days (~{len(parsed)/span:.2f} posts/day)",
                reference="post", confidence=0.5,
            ))
        repeated = self._repeated_themes(items)
        if repeated:
            signals.append(ContextSignal(
                trait="repeated_themes",
                description="recurring terms across posts: " + ", ".join(repeated[:5]),
                reference="post", confidence=0.5,
            ))
        return signals

    def _build_user_prompt(self, profile, content):
        lines = []
        for ref, text, ts in collect_content_items(profile):
            label = f"[{ref}" + (f", {ts}" if ts else "") + "]"
            lines.append(f"{label}: {text}")
        obs = "\n".join(f"- [{o.reference}] {o.text}" for o in content.observations) or "(none)"
        return (
            f"Public profile:\nusername: {profile.username}\n"
            f"display name: {profile.display_name or 'unavailable'}\n"
            f"followers: {profile.follower_count or 'unavailable'} | following: {profile.following_count or 'unavailable'} | posts: {profile.post_count or 'unavailable'}\n"
            f"private: {'yes' if profile.is_private else 'no'}\n\n"
            "Content items:\n" + "\n".join(lines) + "\n\nObservations:\n" + obs
        )

    def _parse_discourse(self, data):
        if not isinstance(data, dict):
            raise ValueError("Malformed context output: expected JSON object.")
        raw = data.get("discourse_modes")
        if not isinstance(raw, list):
            raise ValueError("Malformed context output: 'discourse_modes' missing.")
        modes = []
        for entry in raw[:12]:
            if not isinstance(entry, dict):
                continue
            mode = str(entry.get("mode") or "").strip()
            if mode not in DISCOURSE_MODES:
                continue
            try:
                conf = float(entry.get("confidence") or 0.0)
            except (TypeError, ValueError):
                conf = 0.0
            modes.append(DiscourseMode(
                mode=mode,
                detail=str(entry.get("detail") or "").strip()[:200] or None,
                confidence=max(0.0, min(1.0, conf)),
            ))
        if raw and not modes:
            raise ValueError("No valid discourse modes in model output.")
        return modes

    @staticmethod
    def _repeated_themes(items):
        texts = [t.lower() for _r, t, _ts in items if t]
        docs = [set(re.findall(r"[a-z0-9]{3,}", t)) for t in texts if t.strip()]
        if len(docs) < 2:
            return []
        counter = Counter()
        for tokens in docs:
            for tok in tokens:
                if tok not in _STOPWORDS:
                    counter[tok] += 1
        repeated = [t for t, c in counter.items() if c >= 2]
        repeated.sort(key=lambda t: (-counter[t], t))
        return repeated[:8]