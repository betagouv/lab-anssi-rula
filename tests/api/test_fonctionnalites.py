from datetime import date

from fastapi.testclient import TestClient

PAYLOAD = {
    "identite_id": 1,
    "produit_id": 1,
    "date_entretien": str(date(2024, 1, 15)),
    "contenu": "Contenu du transcript.",
}


def _creer_transcript(client: TestClient) -> int:
    return client.post("/api/transcripts", json=PAYLOAD).json()["id"]


def test_calculer_cree_fonctionnalites(client: TestClient) -> None:
    tid = _creer_transcript(client)
    r = client.post(f"/api/fonctionnalites/transcripts/{tid}")
    assert r.status_code == 201
    assert len(r.json()) == 2
    assert r.json()[0]["transcript_id"] == tid
    assert r.json()[0]["contenu"] == "Fonctionnalité A"
    assert r.json()[1]["contenu"] == "Fonctionnalité B"


def test_calculer_retourne_409_si_deja_existantes(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/fonctionnalites/transcripts/{tid}")
    r = client.post(f"/api/fonctionnalites/transcripts/{tid}")
    assert r.status_code == 409


def test_calculer_retourne_404_si_transcript_inconnu(client: TestClient) -> None:
    r = client.post("/api/fonctionnalites/transcripts/999")
    assert r.status_code == 404


def test_obtenir_fonctionnalites(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/fonctionnalites/transcripts/{tid}")
    r = client.get(f"/api/fonctionnalites/transcripts/{tid}")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["transcript_id"] == tid


def test_obtenir_fonctionnalites_retourne_404_si_absentes(client: TestClient) -> None:
    tid = _creer_transcript(client)
    r = client.get(f"/api/fonctionnalites/transcripts/{tid}")
    assert r.status_code == 404


def test_lister_fonctionnalites_vide(client: TestClient) -> None:
    r = client.get("/api/fonctionnalites")
    assert r.status_code == 200
    assert r.json() == []


def test_lister_fonctionnalites(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/fonctionnalites/transcripts/{tid}")
    r = client.get("/api/fonctionnalites")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert all(f["transcript_id"] == tid for f in r.json())
