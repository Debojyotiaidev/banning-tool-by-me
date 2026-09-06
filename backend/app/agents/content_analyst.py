"""Content Analyst role.

Reads publicly accessible content items (bio + public captions) and produces
verifiable *observations*. It deliberately does NOT make policy decisions and
never invents evidence: every observation must carry a quote that can be
found verbatim in the collected data, otherwise it is discarded.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from ..models.schemas import ContentAnalysis, ContentObservation, InstagramProfile


def collect_content_items(
    profile: InstagramProfile,
) -> List[Tuple[str, str, Optional[str]]]:
    """Return ``(reference, text, timestamp)`` for publicly accessible items.

    The bio is always public profile-level information. Posts are only used
    when the account is public -- private posts/stories/highlights are never
    retrieved or analyzed.
    """
    items: List[Tuple[str, str, Optional[str]]] = []
    if profile.bio and profile.bio not in ("", "Unavailable"):
        items.append(("bio", profile.bio, None))
    if not profile.is_private and profile.recent_posts:
        for index, post in enumerate(profile.recent_posts, start=1):
            caption = (post.get("caption") or "").strip()
            if caption:
                items.append((f"post#{index}", caption, post.get("timestamp")))
    return items


def reduce_text(text: str, limit: int = 160) -> str:
    """Keep a plain-text excerpt short without inventing anything."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


class ContentAnalyst:
    """Extracts observable, verifiable content observations (no verdicts)."""

    SYSTEM_PROMPT = (
        "You are the Content Analyst component of 'Sonics', a read-only "
        "Instagram policy and evidence analysis tool.\n"
        "You analyze ONLY the publicly accessible content supplied in the "
        "user message. You DO NOT make policy decisions.\n"
        "Rules:\n"
        "- Base every observation on text that actually appears in the supplied content.\n"
        "- Every observation MUST include a short exact 'quote' that appears "
        "verbatim in the referenced item; observations without a verifiable "
        "quote will be discarded.\n"
        "- Never invent, guess, or extrapolate content.\n"
        "- Do not speculate about the account owner's personal identity.\n"
        "Return ONLY JSON (no prose) in exactly this shape:\n"
        '{"observations": [{"reference": "bio", "quote": "...", "text": "...", '
        '"content_signal": "...", "context_clue": "...", "confidence": 0.0}]}\n'
        '"reference" must match one of the ids in the content list exactly.'
    )

    def __init__(self, provider: object) -> None:
        self.provider = provider

    def analyze(self, profile: InstagramProfile) -> ContentAnalysis:
        items = collect_content_items(profile)
        if not items:
            return ContentAnalysis(
                status="unavailable",
                note="No accessible content available for analysis.",
            )
        lines = []
        for reference, text, timestamp in items:
            label = f"[{reference}"
            if timestamp:
                label += f", {timestamp}"
            label += "]"
            lines.append(f"{label}: {text}")
        user_prompt = "Content items (publicly accessible information only):\n" + "\n".join(lines)
        data = self.provider.generate_json(
            system=self.SYSTEM_PROMPT, user=user_prompt,
            temperature=0.15, max_tokens=1500,
        )
        return self._parse(data, items)

    def _parse(self, data, items):
        if not isinstance(data, dict):
            raise ValueError("Malformed content analysis output: expected a JSON object.")
        raw = data.get("observations")
        if not isinstance(raw, list):
            raise ValueError("Malformed content analysis output: 'observations' missing.")
        id_map = {ref: text for ref, text, _ts in items}
        observations = []
        for entry in raw[:25]:
            if not isinstance(entry, dict):
                continue
            reference = str(entry.get("reference") or "").strip()
            if reference not in id_map:
                continue
            text = str(entry.get("text") or "").strip()
            quote = str(entry.get("quote") or "").strip()
            source_text = id_map[reference].lower()
            verified_quote = None
            if quote and quote.lower() in source_text:
                verified_quote = quote
            elif text and text.lower() in source_text:
                verified_quote = text
            if not verified_quote:
                continue
            try:
                confidence = float(entry.get("confidence") or 0.0)
            except (TypeError, ValueError):
                confidence = 0.0
            observations.append(ContentObservation(
                reference=reference,
                quote=reduce_text(verified_quote, 160),
                text=reduce_text(text or verified_quote, 300),
                content_signal=str(entry.get("content_signal") or "").strip()[:60] or None,
                context_clue=str(entry.get("context_clue") or "").strip()[:160] or None,
                confidence=max(0.0, min(1.0, confidence)),
            ))
        if not observations:
            raise ValueError("No verifiable observations could be extracted from the model output.")
        return ContentAnalysis(observations=observations, status="completed")