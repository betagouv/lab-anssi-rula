from fastapi.testclient import TestClient


def test_lister_vide(client: TestClient):
    assert client.get("/api/transcripts").json() == []


def test_ajouter(client: TestClient):
    reponse = client.post("/api/transcripts", json={
        "identite_id": 1,
        "produit_id": 1,
        "date_entretien": "2026-06-16",
        "contenu": "L'utilisateur a dit que la navigation est confuse.",
    })
    assert reponse.status_code == 201
    data = reponse.json()
    assert data["id"] == 1
    assert data["identite_id"] == 1
    assert data["contenu"] == "L'utilisateur a dit que la navigation est confuse."


def test_lister_apres_ajout(client: TestClient):
    client.post("/api/transcripts", json={
        "identite_id": 1, "produit_id": 1,
        "date_entretien": "2026-06-16", "contenu": "Transcript A",
    })
    client.post("/api/transcripts", json={
        "identite_id": 2, "produit_id": 1,
        "date_entretien": "2026-06-15", "contenu": "Transcript B",
    })
    assert len(client.get("/api/transcripts").json()) == 2
