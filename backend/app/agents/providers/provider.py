"""AI provider implementations for Sonics analysis.

The Ollama provider (``app.agents.providers.ollama``) is the default local-LLM
path. ``LocalAIProvider`` here is the built-in deterministic offline rules
engine used by the fallback path — no API keys, no model downloads.
"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from pydantic import BaseModel

from ...models.policies import normalize_category_name
from ...models.schemas import InstagramProfile


class AnalysisResult(BaseModel):
    """Output of the deterministic offline rules engine (fallback only)."""

    category: str
    classification: str
    confidence: float
    severity: str
    evidence: str
    explanation: str

# ---------------------------------------------------------------------------
# Built-in signal rules (lightweight, deterministic, offline)
# ---------------------------------------------------------------------------

# phrase / pattern -> weight. Higher weight = stronger signal.
_SIGNALS: Dict[str, Dict] = {
    "Spam": {
        "keywords": {
            "follow back": 2, "follow me": 1, "follow4follow": 3, "f4f": 2,
            "dm me": 2, "link in bio": 2, "click the link": 3, "buy now": 1,
            "order now": 1, "limited time": 1, "act now": 1, "100% guaranteed": 2,
            "giveaway": 2, "winner": 1, "promo": 1, "discount": 1, "cheap": 1,
            "cashapp": 2, "paypal": 2, "bitcoin": 2, "crypto": 1,
            "auto follower": 3, "get followers": 3, "buy followers": 4,
            "buy likes": 3, "boost your": 2,
        },
        "patterns": [
            (r"@[A-Za-z0-9._]+", "mentions @handles", 0.3),
            (r"(?:#\w+\s*){6,}", "excessive hashtags", 1),
            (r"https?://\S+", "external link", 0.5),
        ],
    },
    "Bullying & Harassment": {
        "keywords": {
            "kill yourself": 4, "kys": 3, "shut up": 2, "you're ugly": 3,
            "you are ugly": 3, "you're stupid": 2, "you are stupid": 2,
            "you're dumb": 2, "you are dumb": 2, "loser": 2, "idiot": 2,
            "worthless": 3, "nobody likes you": 3, "get a life": 2,
            "you're a joke": 3, "you are a joke": 3, "pathetic": 2,
            "nobody cares": 1, "uninstall": 1,
        },
        "patterns": [
            (r"\b(?:kill|hurt|destroy|end)\s+(?:you|him|her|them)\b", "threat language", 3),
        ],
    },
    "Hateful Conduct": {
        "keywords": {
            "white power": 3, "white supremacy": 3, "kill all": 4,
            "exterminate": 4, "heil": 3, "race war": 4, "racial purity": 4,
            "you people": 2, "foreigners out": 3, "go back to your country": 3,
            "inferior race": 4, "superior race": 4,
        },
        "patterns": [
            (r"\b(?:hate|attack|ban)\s+[a-z\s]{0,20}\b(?:race|religion|gender|group)", "identity-targeted hostility", 3),
        ],
    },
    "Impersonation": {
        "keywords": {
            "official only": 2, "only official": 2, "official page": 2,
            "fake account": 3, "real account": 1, "verified": 1, "legit": 1,
            "dm for booking": 2, "manager dm": 2, "contact my manager": 2,
            "official agent": 2, "click to verify": 3, "verify your account": 3,
            "fan page": 1, "not affiliated": 1, "personal account": 1,
        },
        "patterns": [],
    },
    "Fraud / Scams / Deceptive Practices": {
        "keywords": {
            "hacking service": 3, "hack instagram": 3, "hacked account": 2,
            "fraud": 2, "scam": 3, "identity theft": 3, "stolen": 2,
            "fake id": 3, "counterfeit": 3, "lottery": 2, "inheritance": 1,
            "free vbucks": 3, "free robux": 3,
        },
        "patterns": [],
    },
    "Restricted Goods & Services": {
        "keywords": {
            "sell drugs": 4, "drugs for sale": 4, "weapons for sale": 4,
            "firearms": 2,
        },
        "patterns": [],
    },
}

_CLASS_TO_SEVERITY = {
    "No Clear Violation": "Low",
    "Low Risk": "Low",
    "Potential Risk": "Medium",
    "High Risk": "High",
    "Unavailable": "Unavailable",
}

# Numeric lift used when aggregating category results into an account score.
_CLASS_VALUE = {
    "No Clear Violation": 0.02,
    "Low Risk": 0.25,
    "Potential Risk": 0.55,
    "High Risk": 0.85,
    "Unavailable": 0.0,
}
def _rule_based_analysis(content_data: str, category: str) -> AnalysisResult:
    """Run the built-in offline signals engine for one category."""
    # Route the category through the centralized taxonomy first so legacy
    # names can never surface inconsistent labels in fallback output.
    category = normalize_category_name(category)
    content = (content_data or "").strip()
    if not content:
        return AnalysisResult(
            category=category,
            classification="Unavailable",
            confidence=0.0,
            severity="Unavailable",
            evidence="Unavailable",
            explanation="No accessible content available for analysis.",
        )

    text_lower = content.lower()
    spec = _SIGNALS.get(category, {"keywords": {}, "patterns": []})

    score = 0.0
    hits: List[Tuple[str, int, float]] = []  # (label, occurrences, weight)

    for phrase, weight in spec["keywords"].items():
        count = text_lower.count(phrase)
        if count:
            capped = min(count, 3)
            score += weight * capped
            hits.append((phrase, capped, weight))

    for regex, label, weight in spec["patterns"]:
        matches = re.findall(regex, content)
        if matches:
            capped = min(len(matches), 3)
            score += weight * capped
            hits.append((label, capped, weight))

    if score <= 0:
        classification = "No Clear Violation"
    elif score <= 2:
        classification = "Low Risk"
    elif score <= 5:
        classification = "Potential Risk"
    else:
        classification = "High Risk"

    severity = _CLASS_TO_SEVERITY.get(classification, "Low")

    # Confidence grows with the amount of evaluated content and matched signals.
    base_conf = 0.55 + 0.06 * len(hits)
    content_boost = min(0.15, len(content) / 3000)
    confidence = round(min(0.95, base_conf + content_boost), 2)
    if not hits:
        confidence = round(min(0.95, 0.5 + content_boost), 2)

    evidence = "Unavailable"
    if hits:
        label, _, _ = hits[0]
        idx = text_lower.find(label)
        if idx >= 0:
            start = max(0, idx - 40)
            end = idx + max(len(label) * 2, 40)
            snippet = content[start:end].replace("\n", " ").strip()
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            evidence = snippet

    matched = ", ".join(f"{h[0]} (x{h[1]})" for h in hits[:4])
    explanation = (
        f"Accessible-content analysis for '{category}': {classification.lower()} "
        f"({len(hits)} signal(s) observed)."
    )
    if matched:
        explanation += f" Signals: {matched}."

    return AnalysisResult(
        category=category,
        classification=classification,
        confidence=confidence,
        severity=severity,
        evidence=evidence,
        explanation=explanation,
    )


def _rule_based_summary(profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
    """Combine per-category results into an account-level model assessment."""
    if not analyses:
        return {
            "overall_score": 0.0,
            "detected_categories": [],
            "severity": "Unavailable",
            "confidence": 0.0,
            "items_analyzed": len(profile.recent_posts),
            "summary": "No analysis data available.",
        }

    weighted = 0.0
    total_w = 0.0
    for result in analyses:
        base = _CLASS_VALUE.get(result.classification, 0.0)
        weight = max(result.confidence, 0.1)
        weighted += base * weight
        total_w += weight

    overall = round(weighted / total_w, 3) if total_w else 0.0
    detected = [
        a.category for a in analyses
        if _CLASS_VALUE.get(a.classification, 0.0) >= 0.4
    ]
    if overall >= 0.55:
        severity = "High"
    elif overall >= 0.25:
        severity = "Medium"
    else:
        severity = "Low"

    avg_conf = sum(a.confidence for a in analyses) / len(analyses)
    confidence = round(min(0.95, avg_conf * 0.9), 2)

    items = len(profile.recent_posts) if profile.recent_posts else 0
    if items == 0 and profile.bio and profile.bio not in ("", "Unavailable"):
        items = 1

    if detected:
        summary = (
            f"Account-level assessment: {severity.lower()} risk "
            f"(overall score {overall * 100:.1f}%). Signals observed in: "
            f"{', '.join(detected)}."
        )
    else:
        summary = (
            f"Account-level assessment: {severity.lower()} risk "
            f"(overall score {overall * 100:.1f}%). No strong signals detected "
            f"in the accessible content."
        )

    return {
        "overall_score": overall,
        "detected_categories": detected,
        "severity": severity,
        "confidence": confidence,
        "items_analyzed": items,
        "summary": summary,
    }


class AIProvider(ABC):
    @abstractmethod
    def analyze_text(self, content_data: str, category: str) -> AnalysisResult:
        pass

    @abstractmethod
    def generate_summary(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        pass


class LocalAIProvider(AIProvider):
    """Default provider — built-in offline rules engine. No keys, no downloads."""

    def analyze_text(self, content_data: str, category: str) -> AnalysisResult:
        return _rule_based_analysis(content_data, category)

    def generate_summary(self, profile: InstagramProfile, analyses: List[AnalysisResult]) -> dict:
        return _rule_based_summary(profile, analyses)


def get_provider() -> AIProvider:
    """Select the AI provider from the ``AI_PROVIDER`` environment variable.

    Default is ``ollama`` -- a local LLM served via the Ollama HTTP API.
    ``local`` selects the deterministic offline rules engine.
    """
    provider_type = os.getenv("AI_PROVIDER", "ollama").lower().strip()

    if provider_type == "ollama":
        from .ollama import OllamaAIProvider

        return OllamaAIProvider()

    return LocalAIProvider()