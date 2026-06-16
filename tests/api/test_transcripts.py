from fastapi.testclient import TestClient

PAYLOAD = {
    "identite_id": 1,
    "produit_id": 1,
    "date_entretien": "2026-06-16",
    "contenu": "L'utilisateur a dit que la navigation est confuse.",
}


def test_lister_vide(client: TestClient):
    assert client.get("/api/transcripts").json() == []


def test_ajouter(client: TestClient):
    reponse = client.post("/api/transcripts", json=PAYLOAD)
    assert reponse.status_code == 201
    data = reponse.json()
    assert data["id"] == 1
    assert data["identite_id"] == 1
    assert data["contenu"] == PAYLOAD["contenu"]


def test_lister_apres_ajout(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    client.post("/api/transcripts", json={**PAYLOAD, "identite_id": 2, "contenu": "Transcript B"})
    assert len(client.get("/api/transcripts").json()) == 2


def test_obtenir(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.get("/api/transcripts/1")
    assert reponse.status_code == 200
    assert reponse.json()["id"] == 1


def test_obtenir_inexistant(client: TestClient):
    assert client.get("/api/transcripts/999").status_code == 404


def test_modifier(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.put("/api/transcripts/1", json={**PAYLOAD, "contenu": "Nouveau contenu"})
    assert reponse.status_code == 200
    assert reponse.json()["contenu"] == "Nouveau contenu"


def test_modifier_inexistant(client: TestClient):
    assert client.put("/api/transcripts/999", json=PAYLOAD).status_code == 404


def test_supprimer(client: TestClient):
    client.post("/api/transcripts", json=PAYLOAD)
    reponse = client.delete("/api/transcripts/1")
    assert reponse.status_code == 204
    assert client.get("/api/transcripts").json() == []


def test_supprimer_inexistant(client: TestClient):
    assert client.delete("/api/transcripts/999").status_code == 404
