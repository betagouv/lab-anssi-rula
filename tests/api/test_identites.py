from fastapi.testclient import TestClient


def test_lister_vide(client: TestClient):
    assert client.get("/api/identites").json() == []


def test_ajouter(client: TestClient):
    reponse = client.post("/api/identites", json={"nom": "Alice"})
    assert reponse.status_code == 201
    assert reponse.json() == {"id": 1, "nom": "Alice"}


def test_lister_apres_ajout(client: TestClient):
    client.post("/api/identites", json={"nom": "Alice"})
    client.post("/api/identites", json={"nom": "Bob"})
    assert len(client.get("/api/identites").json()) == 2
