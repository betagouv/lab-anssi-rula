from fastapi.testclient import TestClient


def test_lister_vide(client: TestClient) -> None:
    r = client.get("/api/idees")
    assert r.status_code == 200
    assert r.json() == []


def test_sync_retourne_les_idees(client: TestClient) -> None:
    r = client.post("/api/idees/sync")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["titre"] == "Idée A"
    assert r.json()[0]["nb_votes"] == 10
    assert r.json()[1]["titre"] == "Idée B"
    assert r.json()[1]["nb_votes"] == 5


def test_sync_idempotent(client: TestClient) -> None:
    client.post("/api/idees/sync")
    r = client.post("/api/idees/sync")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_lister_apres_sync(client: TestClient) -> None:
    client.post("/api/idees/sync")
    r = client.get("/api/idees")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["nb_votes"] >= r.json()[1]["nb_votes"]
