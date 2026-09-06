from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Banning Tool API is running"}


def test_analyze_invalid_username():
    response = client.post("/api/analyze", json={"username": "!! not valid !!"})
    assert response.status_code == 400


@patch("app.instagram.client.InstagramClient.get_profile", return_value=None)
def test_analyze_not_found(mock_get_profile):
    # Offline-safe: get_profile is mocked so no network call is made.
    # The endpoint should return a 200 with an "Account not found" status
    # rather than erroring out.
    response = client.post("/api/analyze", json={"username": "non_existent_user_1234567890"})
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["username"] == "non_existent_user_1234567890"
    assert "not found" in data["profile"]["access_status"].lower()


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
