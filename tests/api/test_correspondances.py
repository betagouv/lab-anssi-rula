from fastapi.testclient import TestClient


def test_analyser_regroupe_les_proches(client: TestClient) -> None:
    r = client.post("/api/correspondances/analyser")
    assert r.status_code == 200
    clusters = r.json()
    assert len(clusters) == 3
    assert clusters[0]["occurrences"] == 2
    assert clusters[0]["libelle"] == "Libellé généré"
    assert {m["texte"] for m in clusters[0]["membres"]} == {"Accès prestataire", "Accès spécifique prestataire"}
    assert clusters[1]["occurrences"] == 1
    assert clusters[1]["membres"][0]["texte"] == "Export PDF"
    assert clusters[1]["membres"][0]["source_id"] == 1
    assert clusters[2]["occurrences"] == 1
    assert clusters[2]["membres"][0]["texte"] == "Vue d'ensemble participants"
    assert clusters[2]["membres"][0]["source"] == "retour_bizdev"
    assert clusters[2]["membres"][0]["source_id"] == 1


def test_analyser_libelle_et_source(client: TestClient) -> None:
    clusters = client.post("/api/correspondances/analyser").json()
    assert clusters[0]["libelle"] == "Libellé généré"
    assert {m["source"] for m in clusters[0]["membres"]} == {"transcript"}
    assert clusters[1]["membres"][0]["source"] == "idee"


def test_analyser_idempotent(client: TestClient) -> None:
    client.post("/api/correspondances/analyser")
    r = client.post("/api/correspondances/analyser")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_charger_vide_avant_analyse(client: TestClient) -> None:
    r = client.get("/api/correspondances")
    assert r.status_code == 200
    assert r.json() == []


def test_charger_retourne_derniere_analyse(client: TestClient) -> None:
    client.post("/api/correspondances/analyser")
    r = client.get("/api/correspondances")
    assert r.status_code == 200
    assert len(r.json()) == 3
    assert {m["texte"] for m in r.json()[0]["membres"]} == {"Accès prestataire", "Accès spécifique prestataire"}
