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


def test_analyser_cree_analyse(client: TestClient) -> None:
    tid = _creer_transcript(client)
    r = client.post(f"/api/analyses/transcripts/{tid}")
    assert r.status_code == 201
    assert r.json()["transcript_id"] == tid
    assert r.json()["contenu"] == "Analyse générée"


def test_analyser_retourne_409_si_deja_existante(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/analyses/transcripts/{tid}")
    r = client.post(f"/api/analyses/transcripts/{tid}")
    assert r.status_code == 409


def test_analyser_retourne_404_si_transcript_inconnu(client: TestClient) -> None:
    r = client.post("/api/analyses/transcripts/999")
    assert r.status_code == 404


def test_obtenir_analyse(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/analyses/transcripts/{tid}")
    r = client.get(f"/api/analyses/transcripts/{tid}")
    assert r.status_code == 200
    assert r.json()["transcript_id"] == tid


def test_obtenir_analyse_retourne_404_si_absente(client: TestClient) -> None:
    tid = _creer_transcript(client)
    r = client.get(f"/api/analyses/transcripts/{tid}")
    assert r.status_code == 404


def test_lister_analyses_vide(client: TestClient) -> None:
    r = client.get("/api/analyses")
    assert r.status_code == 200
    assert r.json() == []


def test_lister_analyses(client: TestClient) -> None:
    tid = _creer_transcript(client)
    client.post(f"/api/analyses/transcripts/{tid}")
    r = client.get("/api/analyses")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["transcript_id"] == tid
