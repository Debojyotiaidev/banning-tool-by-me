"""Sonics analysis pipeline.

Orchestrates the five-role architecture:
1. Content Analyst  -> 2. Context/Behavior Analyst  -> 3. Policy Category Analyst
4. Evidence Verifier  -> 5. Final Judge / Aggregator

The pipeline is read-only and never produces ban/enforcement probabilities.
"""
from __future__ import annotations

from typing import List, Optional

from ..models.schemas import (
    CandidateCategory, CategoryScan, ContentAnalysis, ContentObservation,
    ContextAnalysis, InstagramProfile, PolicyAnalysisResponse, VerifiedFinding,
)
from .content_analyst import ContentAnalyst, collect_content_items
from .context_analyst import ContextBehaviorAnalyst
from .evidence_verifier import EvidenceVerifier
from .judge import FinalJudge
from .policy_analyst import PolicyCategoryAnalyst
from .providers.ollama import OllamaError  # noqa: F401
from .providers.provider import LocalAIProvider, get_provider

_FALLBACK_RULES_MAP = [
    ("Spam", "Spam"),
    ("Impersonation", "Impersonation Risk"),
    ("Bullying & Harassment", "Harassment / Bullying"),
    ("Hateful Conduct", "Hate Speech"),
    ("Other Policy Areas", "General Policy Risk"),
]


class AnalysisPipeline:
    """Runs the full five-role analysis pipeline."""

    def __init__(self, provider=None):
        self.provider = provider if provider is not None else get_provider()

    def run(self, profile):
        notes = []
        private = bool(getattr(profile, "is_private", False))
        had_content = bool(self._content_text(profile).strip())
        if private:
            notes.append("Account is private: analysis limited to publicly visible profile-level information only.")

        # Deterministic-only engine (AI_PROVIDER=local) — skip all LLM calls.
        if not hasattr(self.provider, "generate_json"):
            return self._run_deterministic(profile, notes)

        # Steps 1-3: run each analyst; collect exceptions without crashing.
        failures = []
        content = self._attempt(lambda: ContentAnalyst(self.provider).analyze(profile), failures, "Content Analyst")
        context = self._attempt(
            lambda: ContextBehaviorAnalyst(self.provider).analyze(profile, content) if content else None,
            failures, "Context/Behavior Analyst",
        )
        scan = self._attempt(
            lambda: PolicyCategoryAnalyst(self.provider).scan(profile, content, context) if content and context else None,
            failures, "Policy Category Analyst",
        )

        # If any LLM step failed and there IS content, use deterministic fallback.
        degraded = bool(failures) and had_content
        if failures and had_content:
            notes.extend(failures)
            notes.append(
                "Ollama unavailable or an LLM step failed: the deterministic "
                "fallback rules engine was used instead. The fallback is NOT "
                "an LLM and its results are more limited."
            )
            content = self._build_fallback_content(profile)
            ctx_sigs = ContextBehaviorAnalyst(self.provider).metrics(profile, content)
            context = ContextAnalysis(signals=ctx_sigs, discourse_modes=[], status="unavailable", note="Fallback.")
            scan = self._fallback_scan(profile, content)
        elif content is None:
            content = ContentAnalysis(status="unavailable", note="Content analysis unavailable.")
        elif context is None:
            context = ContextAnalysis(status="unavailable", note="Context analysis unavailable.")
        elif scan is None:
            scan = CategoryScan(status="unavailable", note="Policy scan unavailable.")

        # Step 4: Evidence Verifier
        verifier = EvidenceVerifier(self.provider)
        try:
            verified = verifier.verify(profile, content, context, scan)
        except Exception as exc:
            notes.append(f"Evidence verification failed ({exc.__class__.__name__}: {exc}).")
            verified = []
        if verifier.note:
            notes.append(verifier.note)

        # Step 5: Final Judge
        limited = private or not had_content
        provider_name = "fallback-rules" if degraded else "ollama"
        return FinalJudge().judge(
            profile=profile, content=content, context=context, scan=scan,
            verified=verified, notes=notes, degraded=degraded,
            limited=limited, provider_name=provider_name,
        )

    @staticmethod
    def _attempt(fn, failures, name):
        try:
            return fn()
        except Exception as exc:
            failures.append(f"{name} failed ({exc.__class__.__name__}: {exc}).")
            return None

    def _run_deterministic(self, profile, notes):
        notes.append("AI_PROVIDER=local: the offline rules engine was used (NOT an LLM).")
        content = self._build_fallback_content(profile)
        if not content.observations:
            limited = bool(getattr(profile, "is_private", False)) or not self._content_text(profile).strip()
            return FinalJudge().judge(
                profile, content, ContextAnalysis(status="unavailable"), CategoryScan(status="unavailable"),
                [], notes=notes, degraded=False, limited=limited, provider_name="local",
            )
        ctx = ContextAnalysis(
            signals=ContextBehaviorAnalyst(self.provider).metrics(profile, content),
            discourse_modes=[], status="completed",
        )
        scan = self._fallback_scan(profile, content)
        verifier = EvidenceVerifier(self.provider)
        verified = verifier.verify(profile, content, ctx, scan)
        if verifier.note:
            notes.append(verifier.note)
        limited = bool(getattr(profile, "is_private", False)) or not self._content_text(profile).strip()
        return FinalJudge().judge(profile, content, ctx, scan, verified, notes=notes, degraded=False, limited=limited, provider_name="local")

    def _content_text(self, profile):
        return "\n".join(t for _r, t, _ts in collect_content_items(profile))

    def _build_fallback_content(self, profile):
        combined = self._content_text(profile).strip()
        if not combined:
            return ContentAnalysis(status="unavailable", note="No accessible content.")
        local = LocalAIProvider()
        observations = []
        for policy_name, rules_key in _FALLBACK_RULES_MAP:
            try:
                result = local.analyze_text(combined, rules_key)
            except Exception:
                continue
            if result.classification not in ("Low Risk", "Potential Risk", "High Risk"):
                continue
            snippet = (result.evidence or "").strip()
            if not snippet or snippet == "Unavailable":
                continue
            if not self._contains_in_combined(snippet, combined):
                continue
            observations.append(ContentObservation(
                reference="content", quote=snippet[:160],
                text=f"Deterministic rule '{rules_key}' matched: {snippet[:220]}",
                content_signal=rules_key, confidence=result.confidence,
            ))
        if not observations:
            return ContentAnalysis(status="unavailable", note="No deterministic signals matched.")
        return ContentAnalysis(observations=observations, status="unavailable", note="Built by deterministic fallback engine.")

    def _contains_in_combined(self, snippet, combined):
        """Whitespace-insensitive substring test.

        The deterministic engine may normalize newlines/whitespace in its
        evidence snippet; collapse runs of any whitespace on both sides so we
        only accept evidence whose words appear verbatim.
        """
        import re
        norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
        return bool(snippet) and norm(snippet) in norm(combined)

    def _fallback_scan(self, profile, content):
        candidates = []
        for obs in content.observations:
            pname = next((p for p, r in _FALLBACK_RULES_MAP if r == obs.content_signal), None)
            if pname is None:
                continue
            candidates.append(CandidateCategory(
                category=pname, relevant=True,
                rationale=f"Deterministic fallback matched '{obs.content_signal}' (Ollama unavailable; NOT an LLM).",
                evidence_refs=[obs.reference], initial_confidence=max(0.5, obs.confidence),
            ))
        return CategoryScan(candidates=candidates, status="completed", note="Deterministic fallback scan.")