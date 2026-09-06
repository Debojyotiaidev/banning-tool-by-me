"""Final Judge / Aggregator role.

Combines outputs from all upstream roles into the final structured
evidence-confidence assessment.
"""
from __future__ import annotations

from typing import List, Optional

from ..models.schemas import (
    CategoryScan, ContentAnalysis, ContextAnalysis, InstagramProfile,
    Observation, PolicyAnalysisResponse, PolicyAssessment, Uncertainty, VerifiedFinding,
)


def _severity(confidence, evidence):
    strengths = [e.strength for e in evidence]
    if confidence >= 70 or any(s == "strong" for s in strengths):
        return "high"
    if confidence >= 45:
        return "medium"
    return "low"


class FinalJudge:
    def judge(self, profile, content, context, scan, verified,
              notes=None, degraded=False, limited=False, provider_name="ollama"):
        notes = list(notes or [])
        cand_map = {c.category: c for c in scan.candidates}
        assessments = []
        for finding in verified:
            if not finding.accepted:
                continue
            cand = cand_map.get(finding.category)
            initial = cand.initial_confidence if cand else 0.0
            strengths = [e.strength for e in finding.evidence]
            bonus = 8.0 if (strengths and all(s == "strong" for s in strengths)) else (
                -6.0 if (strengths and not any(s == "strong" for s in strengths) and any(s == "weak" for s in strengths)) else 0.0
            )
            conf = round(min(98.0, max(2.0, initial * 100 + finding.confidence_adjustment * 100 + bonus)), 1)
            reasoning = (cand.rationale if cand and cand.rationale else "Evidence observed in collected public content.")
            if degraded:
                reasoning += " NOTE: produced via the deterministic fallback engine (Ollama unavailable); NOT an LLM assessment."
            assessments.append(PolicyAssessment(
                rank=0, category=finding.category, confidence=conf,
                severity=_severity(conf, finding.evidence),
                evidence=finding.evidence, reasoning=reasoning,
                context=self._context_summary(context), verification=finding.verification,
            ))
        assessments.sort(key=lambda a: (-a.confidence, -len(a.evidence)))
        for i, a in enumerate(assessments, 1):
            a.rank = i
        status = "degraded" if degraded else ("limited" if limited else "completed")
        return PolicyAnalysisResponse(
            policy_categories=assessments,
            overall_observations=self._obs(content, context),
            uncertainties=self._uncert(profile, content, degraded, limited, notes, assessments),
            analysis_status=status, provider=provider_name, notes=notes,
        )

    def _context_summary(self, context):
        parts = []
        if context.discourse_modes:
            parts.append("discourse: " + ", ".join(m.mode for m in context.discourse_modes[:3]))
        if context.signals:
            parts.append("signals: " + "; ".join(s.trait for s in context.signals[:3]))
        return ". ".join(parts) or "no significant context signals"

    def _obs(self, content, context):
        observations = []
        for o in content.observations[:6]:
            observations.append(Observation(aspect=o.content_signal or "content", detail=o.text, reference=o.reference))
        for s in context.signals[:3]:
            observations.append(Observation(aspect=s.trait, detail=s.description, reference=s.reference))
        return observations

    def _uncert(self, profile, content, degraded, limited, notes, assessments):
        u = []
        if degraded:
            u.append(Uncertainty(factor="provider", detail="Ollama unavailable; results use the deterministic fallback rules engine, which is not an LLM."))
        if limited:
            u.append(Uncertainty(factor="data_availability", detail="Only publicly available information was analyzed."))
        if profile.is_private:
            u.append(Uncertainty(factor="data_availability", detail="Private posts, stories, and highlights were not retrieved."))
        if content.observations and len(content.observations) < 3:
            u.append(Uncertainty(factor="sample_size", detail="Few content items available; confidence may be less robust."))
        if not content.observations and not assessments:
            u.append(Uncertainty(factor="interpretation", detail="No policy category met the evidence bar. Absence of detected signals is not compliance confirmation."))
        for note in notes:
            if "unavailable" in note.lower() or "skipped" in note.lower():
                u.append(Uncertainty(factor="process", detail=note))
        return u[:6]