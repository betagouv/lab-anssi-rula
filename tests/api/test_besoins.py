from datetime import date

from fastapi.testclient import TestClient

from api.besoins import fabrique_dependances_besoins
from besoins.dependances import DependancesBesoins

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


def test_fabrique_dependances_besoins_transmet_les_dependances_injectees() -> None:
    depot = object()
    depot_transcripts = object()
    depot_fonctionnalites = object()
    service_fonctionnalites = object()
    depot_idees = object()
    depot_retours = object()

    dependances = fabrique_dependances_besoins(
        depot=depot,  # type: ignore[arg-type]
        depot_transcripts=depot_transcripts,  # type: ignore[arg-type]
        depot_fonctionnalites=depot_fonctionnalites,  # type: ignore[arg-type]
        service_fonctionnalites=service_fonctionnalites,  # type: ignore[arg-type]
        depot_idees=depot_idees,  # type: ignore[arg-type]
        depot_retours=depot_retours,  # type: ignore[arg-type]
    )

    assert isinstance(dependances, DependancesBesoins)
    assert dependances.depot is depot
    assert dependances.depot_transcripts is depot_transcripts
    assert dependances.depot_fonctionnalites is depot_fonctionnalites
    assert dependances.service_fonctionnalites is service_fonctionnalites
    assert dependances.depot_idees is depot_idees
    assert dependances.depot_retours is depot_retours


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
