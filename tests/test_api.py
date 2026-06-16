from fastapi.testclient import TestClient

from serveur import app

client = TestClient(app)


def test_sante():
    response = client.get("/api/sante")
    assert response.status_code == 200
    assert response.json() == {"statut": "ok"}
