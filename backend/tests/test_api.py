from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Banning Tool API is running"}

def test_analyze_not_found():
    # This should return a 200 with "Account not found" status rather than erroring
    response = client.post("/analyze", json={"username": "non_existent_user_1234567890"})
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["username"] == "non_existent_user_1234567890"
    assert "not found" in data["profile"]["access_status"].lower()
