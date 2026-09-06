"""Tests for the five-role analysis pipeline."""
from app.agents.evidence_verifier import EvidenceVerifier
from app.agents.pipeline import AnalysisPipeline
from app.agents.providers.ollama import OllamaConnectionError
from app.models.policies import POLICY_CATEGORIES
from app.models.schemas import (
    CandidateCategory, CategoryScan, ContentAnalysis, ContentObservation,
    ContextAnalysis, PolicyAnalysisResponse,
)
from fakes import (
    CONTEXT_RESPONSE, CONTENT_RESPONSE, POLICY_RESPONSE, VERIFIER_RESPONSE,
    FakeProvider, all_content, make_not_found_profile, make_private_profile, make_public_profile,
)

def _full():
    return [CONTENT_RESPONSE, CONTEXT_RESPONSE, POLICY_RESPONSE, VERIFIER_RESPONSE]

def test_taxonomy_covers_all_expected_areas():
    names = {c.name for c in POLICY_CATEGORIES}
    expected = {
        "Spam", "Impersonation", "Bullying & Harassment", "Hateful Conduct",
        "Violence & Incitement", "Dangerous Organizations & Individuals",
        "Coordinating Harm / Promoting Crime", "Human Exploitation",
        "Child Sexual Exploitation", "Adult Sexual Exploitation",
        "Suicide & Self-Injury", "Fraud / Scams / Deceptive Practices",
        "Restricted Goods & Services", "Other Policy Areas",
    }
    assert expected <= names

def test_completed_path_ranks_categories():
    result = AnalysisPipeline(provider=FakeProvider(_full())).run(make_public_profile())
    assert isinstance(result, PolicyAnalysisResponse)
    assert result.analysis_status == "completed"
    assert len(result.policy_categories) == 2
    assert [p.rank for p in result.policy_categories] == [1, 2]
    cats = [p.category for p in result.policy_categories]
    assert "Fraud / Scams / Deceptive Practices" in cats
    assert "Spam" in cats
    for pc in result.policy_categories:
        assert 0 < pc.confidence < 100
        assert pc.evidence
        for ev in pc.evidence:
            assert ev.quote and ev.quote.lower() in all_content(make_public_profile()).lower()

def test_invented_evidence_is_dropped():
    result = AnalysisPipeline(provider=FakeProvider(_full())).run(make_public_profile())
    for pc in result.policy_categories:
        for ev in pc.evidence:
            assert "invented" not in (ev.quote or "").lower()

def test_no_ban_probability_fields():
    result = AnalysisPipeline(provider=FakeProvider(_full())).run(make_public_profile())
    data = result.model_dump()
    assert "estimated_likelihood" not in data
    assert "enforcement_simulation" not in data

def test_no_relevant_categories_valid():
    result = AnalysisPipeline(provider=FakeProvider(
        [CONTENT_RESPONSE, CONTEXT_RESPONSE, {"candidates": []}]
    )).run(make_public_profile())
    assert result.analysis_status == "completed"
    assert result.policy_categories == []

def test_malformed_output_falls_back():
    result = AnalysisPipeline(provider=FakeProvider([{"unexpected": "shape"}])).run(make_public_profile())
    assert result.analysis_status == "degraded"
    assert result.provider == "fallback-rules"
    assert any("NOT an LLM" in n for n in result.notes)

def test_ollama_connection_error_falls_back():
    provider = FakeProvider([OllamaConnectionError("down")] * 6)
    result = AnalysisPipeline(provider=provider).run(make_public_profile())
    assert result.analysis_status == "degraded"
    assert result.provider == "fallback-rules"
    joined = all_content(make_public_profile())
    norm = lambda s: __import__("re").sub(r"\s+", " ", s).lower()
    assert result.policy_categories, "fallback should surface signals"
    for pc in result.policy_categories:
        assert "fallback" in pc.reasoning.lower()
        for ev in pc.evidence:
            assert norm(ev.quote) in norm(joined)

def test_private_account_limited():
    result = AnalysisPipeline(provider=FakeProvider(_full())).run(make_private_profile())
    assert result.analysis_status == "limited"
    assert any("private" in n.lower() for n in result.notes)
    for pc in result.policy_categories:
        for ev in pc.evidence:
            assert not ev.reference.startswith("post")

def test_no_content_no_provider_calls():
    provider = FakeProvider([])
    result = AnalysisPipeline(provider=provider).run(make_not_found_profile())
    assert result.analysis_status == "limited"
    assert result.policy_categories == []
    assert provider.calls == []

def test_local_rules_not_an_llm():
    from app.agents.providers.provider import LocalAIProvider
    result = AnalysisPipeline(provider=LocalAIProvider()).run(make_public_profile())
    assert result.provider == "local"
    assert any("NOT an LLM" in n for n in result.notes)

def test_verifier_accepts_real_evidence():
    verifier = EvidenceVerifier(object())
    profile = make_public_profile()
    content = ContentAnalysis(observations=[
        ContentObservation(reference="bio", quote="Buy followers, link in bio", text="promo", confidence=0.9),
    ])
    scan = CategoryScan(candidates=[
        CandidateCategory(category="Fraud / Scams / Deceptive Practices", relevant=True, rationale="x", evidence_refs=["bio"], initial_confidence=0.7),
    ])
    findings = verifier.verify(profile, content, ContextAnalysis(), scan)
    assert findings[0].accepted is True
    assert findings[0].evidence[0].quote.lower() in all_content(profile).lower()

def test_verifier_rejects_fabricated():
    verifier = EvidenceVerifier(object())
    profile = make_public_profile()
    content = ContentAnalysis(observations=[
        ContentObservation(reference="bio", quote="INVENTED NOT IN BIO", text="x", confidence=0.9),
    ])
    scan = CategoryScan(candidates=[
        CandidateCategory(category="Spam", relevant=True, rationale="x", evidence_refs=["bio"], initial_confidence=0.7),
    ])
    findings = verifier.verify(profile, content, ContextAnalysis(), scan)
    assert findings[0].accepted is False
    assert findings[0].verification == "rejected"