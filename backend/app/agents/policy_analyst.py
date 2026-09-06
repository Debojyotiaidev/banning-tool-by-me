"""Policy Category Analyst role.

Maps verified content observations to the centralized taxonomy. Multiple
categories may be relevant; it is normal for none to be.
"""
from __future__ import annotations

from typing import List

from ..models.policies import POLICY_CATEGORIES, POLICY_NAMES, normalize_category_name
from ..models.schemas import (
    CandidateCategory, CategoryScan, ContentAnalysis, ContextAnalysis, InstagramProfile,
)


class PolicyCategoryAnalyst:
    SYSTEM_PROMPT = (
        "You are the Policy Category Analyst component of 'Sonics', a read-only "
        "Instagram policy and evidence analysis tool.\n"
        "Decide which policy categories are potentially relevant based on the "
        "supplied observations and context.\n"
        "Rules:\n"
        "- Only mark a category relevant when the observations actually support it.\n"
        "- Multiple relevant categories are allowed.\n"
        "- It is completely normal for an account to have NO relevant categories.\n"
        "- Sensitive categories (Child Sexual Exploitation, Dangerous Organizations & "
        "Individuals, etc.) require explicit, direct, strong evidence. Discussing, "
        "reporting, criticizing, condemning, or quoting a topic is NOT evidence.\n"
        "Return ONLY JSON:\n"
        '{"candidates": [{"category": "<exact name>", "relevant": true, '
        '"rationale": "...", "evidence_refs": ["bio"], "initial_confidence": 0.0}]}'
    )

    def __init__(self, provider):
        self.provider = provider

    def scan(self, profile, content, context):
        if not content.observations:
            return CategoryScan(status="unavailable", note="No verifiable observations; scan skipped.")
        user_prompt = self._build_user_prompt(profile, content, context)
        data = self.provider.generate_json(system=self.SYSTEM_PROMPT, user=user_prompt, temperature=0.1, max_tokens=1200)
        return CategoryScan(candidates=self._parse(data, content), status="completed")

    def _build_user_prompt(self, profile, content, context):
        tax = [f"- {c.name}: {c.description}" for c in POLICY_CATEGORIES]
        obs = [f"- id={o.reference} | quote={o.quote!r} | text={o.text}" for o in content.observations]
        modes = [f"- {m.mode} ({m.confidence:.0%}): {m.detail or ''}" for m in context.discourse_modes] or ["(none)"]
        sigs = [f"- {s.trait}: {s.description}" for s in context.signals] or ["(none)"]
        return (
            "Policy taxonomy:\n" + "\n".join(tax) +
            "\n\nContent observations:\n" + "\n".join(obs) +
            "\n\nDiscourse modes:\n" + "\n".join(modes) +
            "\n\nContext signals:\n" + "\n".join(sigs) +
            f"\n\nPrivate account: {'yes' if profile.is_private else 'no'}"
        )

    def _parse(self, data, content):
        if not isinstance(data, dict):
            raise ValueError("Malformed policy scan: expected JSON object.")
        raw = data.get("candidates")
        if not isinstance(raw, list):
            raise ValueError("Malformed policy scan: 'candidates' missing.")
        valid_refs = {o.reference for o in content.observations} | {"content"}
        names = set(POLICY_NAMES)
        candidates = []
        for entry in raw[:20]:
            if not isinstance(entry, dict):
                continue
            # Normalize legacy/alias names from the model into the canonical
            # taxonomy so the output is always internally consistent.
            name = normalize_category_name(str(entry.get("category") or "").strip())
            if name not in names:
                continue
            if not bool(entry.get("relevant")):
                continue
            refs = [str(r) for r in (entry.get("evidence_refs") or []) if str(r) in valid_refs]
            try:
                conf = float(entry.get("initial_confidence") or 0.0)
            except (TypeError, ValueError):
                conf = 0.0
            candidates.append(CandidateCategory(
                category=name, relevant=True,
                rationale=str(entry.get("rationale") or "").strip()[:400] or None,
                evidence_refs=refs,
                initial_confidence=max(0.0, min(1.0, conf)),
            ))
        return candidates