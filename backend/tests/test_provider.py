from app.agents.providers.provider import LocalAIProvider
from app.models.schemas import InstagramProfile


def _make_profile(content: str) -> InstagramProfile:
    return InstagramProfile(
        username="payload_user",
        bio=content,
        recent_posts=[],
        access_status="Public",
    )


def test_local_spam_detection():
    provider = LocalAIProvider()
    result = provider.analyze_text(
        "FREE GIVEAWAY! follow back everyone, link in bio, buy followers cheap!!",
        "Spam",
    )
    assert result.category == "Spam"
    assert result.classification in ("Potential Risk", "High Risk")
    assert result.severity in ("Medium", "High")
    assert result.confidence > 0


def test_local_harassment_detection():
    provider = LocalAIProvider()
    result = provider.analyze_text("you are worthless, nobody likes you, get a life", "Harassment / Bullying")
    assert result.classification in ("Potential Risk", "High Risk")


def test_local_clean_content():
    provider = LocalAIProvider()
    result = provider.analyze_text(
        "Just a peaceful day with my dog at the beach. #nature #sunset",
        "Hate Speech",
    )
    assert result.classification == "No Clear Violation"


def test_local_empty_content():
    provider = LocalAIProvider()
    result = provider.analyze_text("", "Spam")
    assert result.classification == "Unavailable"


def test_local_summary():
    provider = LocalAIProvider()
    profile = _make_profile("FREE FOLLOWERS, follow back, link in bio!!")
    analyses = [
        provider.analyze_text(profile.bio, "Spam"),
        provider.analyze_text(profile.bio, "Hate Speech"),
    ]
    summary = provider.generate_summary(profile, analyses)
    assert "overall_score" in summary
    assert "detected_categories" in summary
    assert isinstance(summary["items_analyzed"], int)
    assert 0.0 <= summary["overall_score"] <= 1.0