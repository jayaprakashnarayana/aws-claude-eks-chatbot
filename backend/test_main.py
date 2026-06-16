import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    # Using the context manager ensures that the startup event runs,
    # which initializes the LLMService.
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    assert "provider" in response.json()
    assert "model_id" in response.json()

def test_chat_validation_empty_messages(client):
    # Test that empty messages list returns 400 (Bad Request)
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 400

def test_chat_validation_invalid_last_role(client):
    # Test that if last message is not user, it returns 400 (Bad Request)
    payload = {
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "how can I help?"}
        ]
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400
    assert "last message in history must be from the user" in response.json()["detail"]
