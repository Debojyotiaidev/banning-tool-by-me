from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.agents.providers.ollama import OllamaConnectionError
from fakes import (
    CONTEXT_RESPONSE,
    CONTENT_RESPONSE,
    POLICY_RESPONSE,
    VERIFIER_RESPONSE,
    FakeProvider,
    make_private_profile,
    make_public_profile,
)

client = TestClient(app)


def _llm_responses():
    return [CONTENT_RESPONSE, CONTEXT_RESPONSE, POLICY_RESPONSE, VERIFIER_RESPONSE]


def test_read_root():
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Banning Tool API is running"}


def test_analyze_invalid_username():
    response = client.post("/api/analyze", json={"username": "!! not valid !!"})
    assert response.status_code == 400


@patch("app.instagram.client.InstagramClient.get_profile", return_value=None)
def test_analyze_not_found(mock_get_profile):
    # Offline-safe: get_profile is mocked, and an empty profile contains no
    # content, so no LLM/network call is attempted.
    response = client.post("/api/analyze", json={"username": "non_existent_user_1234567890"})
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["username"] == "non_existent_user_1234567890"
    assert "not found" in data["profile"]["access_status"].lower()
    assert "analysis" in data
    assert data["analysis"]["analysis_status"] == "limited"
    assert data["analysis"]["policy_categories"] == []
    # Ban-probability outputs must not be produced automatically.
    assert "enforcement_simulation" not in data
    assert "account_risk" not in data


@patch("app.instagram.client.InstagramClient.get_profile", return_value=make_public_profile())
@patch("app.agents.pipeline.get_provider", return_value=FakeProvider(_llm_responses()))
def test_analyze_public_account_new_architecture(mock_get_provider, mock_get_profile):
    response = client.post("/api/analyze", json={"username": "demo_account"})
    assert response.status_code == 200
    data = response.json()
    assert data["access_status"] == "Public"
    analysis = data["analysis"]
    assert analysis["analysis_status"] == "completed"
    assert analysis["policy_categories"]
    assert "enforcement_simulation" not in data
    assert "estimated_likelihood" not in analysis
    for category in analysis["policy_categories"]:
        assert 1 <= category["rank"] <= len(analysis["policy_categories"])
        assert 0 <= category["confidence"] <= 100
        assert category["evidence"]


@patch("app.instagram.client.InstagramClient.get_profile", return_value=make_private_profile())
@patch("app.agents.pipeline.get_provider", return_value=FakeProvider(_llm_responses()))
def test_analyze_private_account_limited(mock_get_provider, mock_get_profile):
    response = client.post("/api/analyze", json={"username": "private_user"})
    assert response.status_code == 200
    data = response.json()
    assert data["access_status"] == "Private"
    analysis = data["analysis"]
    assert analysis["analysis_status"] == "limited"
    assert any("private" in n.lower() for n in analysis["notes"])
    assert "enforcement_simulation" not in data
    for category in analysis["policy_categories"]:
        for evidence in category["evidence"]:
            assert not evidence["reference"].startswith("post")


@patch("app.instagram.client.InstagramClient.get_profile", return_value=make_public_profile())
@patch("app.agents.pipeline.get_provider", return_value=FakeProvider([OllamaConnectionError("down")] * 6))
def test_analyze_ollama_unavailable_degraded(mock_get_provider, mock_get_profile):
    response = client.post("/api/analyze", json={"username": "demo_account"})
    assert response.status_code == 200
    data = response.json()
    analysis = data["analysis"]
    assert analysis["analysis_status"] == "degraded"
    assert analysis["provider"] == "fallback-rules"
    assert any("Ollama unavailable" in n or "LLM step failed" in n for n in analysis["notes"])
    assert any("NOT an LLM" in n for n in analysis["notes"])
    assert "enforcement_simulation" not in data


def test_dashboard_served():
    # The built dashboard must be served at "/" (HTML, not API JSON).
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Sonics" in response.text


def test_simulate_endpoint():
    response = client.post(
        "/api/simulate",
        json={
            "risk": {
                "overall_score": 0.4,
                "detected_categories": ["Spam"],
                "severity": "Medium",
                "confidence": 0.8,
                "items_analyzed": 5,
                "summary": "Test",
            },
            "inputs": {
                "violation_reports": 3,
                "spam_reports": 2,
                "impersonation_reports": 0,
                "reporting_sources": 2,
            },
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert "estimated_likelihood" in result
    assert "factors" in result
