from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    assert "provider" in response.json()
    assert "model_id" in response.json()

def test_chat_validation_empty_messages():
    # Test that empty messages list returns 400
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 422 # FastAPI validation error for empty list / missing field

def test_chat_validation_invalid_last_role():
    # Test that if last message is not user, it returns 400
    payload = {
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "how can I help?"}
        ]
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400
    assert "last message in history must be from the user" in response.json()["detail"]
