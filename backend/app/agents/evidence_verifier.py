"""Evidence Verifier role.

Independently re-checks every proposed policy category against the actual
collected public data. Fabricated or unsupported findings are rejected.
"""
from __future__ import annotations

from typing import List, Optional

from ..models.schemas import (
    CategoryScan, ContentAnalysis, ContextAnalysis, EvidenceItem, InstagramProfile, VerifiedFinding,
)
from .content_analyst import collect_content_items


def _strength_from_confidence(confidence):
    if confidence >= 0.8:
        return "strong"
    if confidence >= 0.55:
        return "moderate"
    return "weak"


class EvidenceVerifier:
    SYSTEM_PROMPT = (
        "You are the Evidence Verifier component of 'Sonics', a read-only "
        "Instagram policy and evidence analysis tool.\n"
        "Review each proposed finding and decide whether to accept or reject it.\n"
        "Check:\n"
        "- Does the cited evidence exist in the collected public data?\n"
        "- Does it genuinely support this category, or is there an innocent, "
        "educational, condemnatory, satirical, or quoted interpretation?\n"
        "- Is the discourse context being misinterpreted?\n"
        "Reject findings that rely on unsupported assumptions.\n"
        'Return ONLY JSON: {"findings": [{"category": "...", "accepted": true, '
        '"confidence_adjustment": 0.0, "rejection_reason": null}]}\n'
        '"confidence_adjustment" must be between -1 and 1.'
    )

    def __init__(self, provider):
        self.provider = provider
        self.note: Optional[str] = None

    def verify(self, profile, content, context, scan):
        self.note = None
        findings = []
        for cand in scan.candidates:
            if not cand.relevant:
                continue
            evidence = self._map_evidence(cand, content, profile)
            if not evidence:
                findings.append(VerifiedFinding(
                    category=cand.category, accepted=False, evidence=[],
                    verification="rejected", rejection_reason="No verifiable evidence in collected public data.",
                ))
                continue
            findings.append(VerifiedFinding(
                category=cand.category, accepted=True, evidence=evidence,
                confidence_adjustment=0.0, verification="verified",
            ))
        self._apply_context_check(scan, findings)
        return findings

    def _content_text(self, profile):
        return "\n".join(t for _r, t, _ts in collect_content_items(profile)).lower()

    @staticmethod
    def _text_contains(text, fragment):
        import re
        norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
        return bool(fragment) and norm(fragment) in norm(text)

    def _map_evidence(self, candidate, content, profile):
        combined = self._content_text(profile)
        obs_map = {o.reference: o for o in content.observations}
        items = []
        for ref in candidate.evidence_refs or []:
            obs = obs_map.get(ref)
            if obs is None:
                continue
            if obs.quote and not self._text_contains(combined, obs.quote):
                continue
            source = "caption" if ref.startswith("post") else ("bio" if ref == ref and ref == "bio" else ("collected_content" if ref == "content" else "post"))
            items.append(EvidenceItem(
                source=source, reference=ref,
                text=(obs.text or "")[:200],
                quote=(obs.quote or "")[:120] or None,
                strength=_strength_from_confidence(obs.confidence),
                relevance=obs.confidence, verification="verified",
            ))
        return items

    def _apply_context_check(self, scan, findings):
        accepted = [f for f in findings if f.accepted]
        if not accepted:
            return
        if not hasattr(self.provider, "generate_json"):
            for f in accepted:
                f.verification = "partially_verified"
            self.note = "LLM-based context verification unavailable; evidence verified deterministically only."
            return
        cand_map = {c.category: c for c in scan.candidates}
        lines = []
        for f in accepted:
            c = cand_map.get(f.category)
            lines.append(f"- {f.category}: rationale={c.rationale if c else ''!r}; refs={[e.reference for e in f.evidence]}")
        user_prompt = "Findings to verify:\n" + "\n".join(lines) + "\n\nPrivate: yes/no"
        try:
            data = self.provider.generate_json(system=self.SYSTEM_PROMPT, user=user_prompt, temperature=0.1, max_tokens=900)
        except Exception as exc:
            for f in accepted:
                f.verification = "partially_verified"
            self.note = f"LLM context check skipped ({exc.__class__.__name__}). Verified deterministically."
            return
        if not isinstance(data, dict):
            for f in accepted:
                f.verification = "partially_verified"
            self.note = "LLM context check skipped (malformed reply)."
            return
        raw = data.get("findings")
        if not isinstance(raw, list):
            for f in accepted:
                f.verification = "partially_verified"
            self.note = "LLM context check skipped (malformed findings)."
            return
        verdicts = {}
        for entry in raw:
            if isinstance(entry, dict) and entry.get("category"):
                verdicts[str(entry["category"])] = entry
        for f in accepted:
            entry = verdicts.get(f.category)
            if not isinstance(entry, dict):
                f.verification = "partially_verified"
                continue
            acc = entry.get("accepted")
            if isinstance(acc, bool):
                f.accepted = acc
            if not f.accepted:
                f.verification = "rejected"
                f.rejection_reason = str(entry.get("rejection_reason") or "Rejected after context review.")[:400]
                continue
            try:
                adj = float(entry.get("confidence_adjustment") or 0.0)
            except (TypeError, ValueError):
                adj = 0.0
            f.confidence_adjustment = max(-1.0, min(1.0, adj))
            f.verification = "verified"