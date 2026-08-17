from datetime import date

from fastapi.testclient import TestClient

TRANSCRIPT = {
    "identite_id": 1,
    "produit_id": 1,
    "date_entretien": str(date(2024, 1, 15)),
    "contenu": "Le suivi des mesures doit être plus simple.",
}
FEATUREBASE_CSV = "Title,Content,Upvote Count,Date\nExport PDF,,10,2024-01-01\n"
BIZDEV_CSV = "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\nIl faut un export,Alice,RSSI,,,,01/01/24,Bob,[ADMIN],Export\n"


def test_lister_besoins_vide_et_filtrer_source(client: TestClient) -> None:
    assert client.get("/api/besoins").json() == []
    assert client.get("/api/besoins?source=idee").json() == []


def test_analyser_besoins_featurebase(client: TestClient) -> None:
    client.post("/api/idees/import", files={"fichier": ("export.csv", FEATUREBASE_CSV.encode(), "text/csv")})

    reponse = client.post("/api/besoins/analyser/idee")

    assert reponse.status_code == 200
    assert len(reponse.json()) == 1
    assert reponse.json()[0]["source"] == "idee"
    assert reponse.json()[0]["nom_generique"] == "Fonctionnalité A"
    assert client.get("/api/besoins?source=idee").json()[0]["texte_original"] == "Export PDF"


def test_analyser_besoins_retours_bizdev(client: TestClient) -> None:
    client.post("/api/retours-bizdev/import", files={"fichier": ("retours.csv", BIZDEV_CSV.encode(), "text/csv")})

    reponse = client.post("/api/besoins/analyser/retour_bizdev")

    assert reponse.status_code == 200
    assert len(reponse.json()) == 1
    assert reponse.json()[0]["source"] == "retour_bizdev"
    assert reponse.json()[0]["verbatim"] == "Il faut un export"


def test_analyser_besoins_transcripts_reutilise_les_fonctionnalites(client: TestClient) -> None:
    transcript_id = client.post("/api/transcripts", json=TRANSCRIPT).json()["id"]

    reponse = client.post("/api/besoins/analyser/transcript")
    seconde_analyse = client.post("/api/besoins/analyser/transcript")

    assert reponse.status_code == 200
    assert seconde_analyse.status_code == 200
    assert len(reponse.json()) == 2
    assert all(b["source"] == "transcript" for b in seconde_analyse.json())
    assert all(b["transcript_id"] == transcript_id for b in seconde_analyse.json())


def test_refuse_une_source_inconnue(client: TestClient) -> None:
    assert client.get("/api/besoins?source=inconnue").status_code == 400
    assert client.post("/api/besoins/analyser/inconnue").status_code == 400
