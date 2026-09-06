"""Smoke test básico. Requer .env configurado e firebase-key.json presente
(mesmo que apontando pra um projeto de teste) pra conseguir importar main.py.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
