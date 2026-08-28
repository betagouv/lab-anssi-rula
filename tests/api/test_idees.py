from fastapi.testclient import TestClient

from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest

CSV_SIMPLE = "Title,Content,Upvote Count,Date\nIdée A,Description A,10,2024-01-01\nIdée B,,5,2024-01-02\n"
CSV_VIDE = "Title,Content,Upvote Count,Date\n"
FORMULAIRE = {"produit_id": "1"}


def test_lister_vide(client: TestClient) -> None:
    r = client.get("/api/idees?produit_id=1")
    assert r.status_code == 200
    assert r.json() == []


def test_import_retourne_les_idees(client: TestClient) -> None:
    r = client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["titre"] == "Idée A: Description A"
    assert r.json()[0]["nb_votes"] == 10
    assert r.json()[1]["titre"] == "Idée B"
    assert r.json()[1]["nb_votes"] == 5


def test_import_sans_confirmation(client: TestClient) -> None:
    r = client.post(
        "/api/idees/import",
        data={"produit_id": "1"},
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_import_ne_consulte_pas_albert(
    client: TestClient, albert_validation: AdaptateurAlbertDeTest
) -> None:
    albert_validation.avec_erreur(RuntimeError("Albert indisponible"))
    r = client.post(
        "/api/idees/import",
        data={"produit_id": "1"},
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    assert r.status_code == 200


def test_import_remplace_les_idees(client: TestClient) -> None:
    client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    csv2 = "Title,Content,Upvote Count,Date\nNouvelle idée,,42,2024-01-03\n"
    r = client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", csv2.encode(), "text/csv")},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["titre"] == "Nouvelle idée"


def test_import_est_isole_par_produit(client: TestClient) -> None:
    client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    client.post(
        "/api/idees/import",
        data={"produit_id": "2", "confirmation": "true"},
        files={"fichier": ("export.csv", CSV_VIDE.encode(), "text/csv")},
    )
    assert len(client.get("/api/idees?produit_id=1").json()) == 2
    assert client.get("/api/idees?produit_id=2").json() == []


def test_import_csv_vide(client: TestClient) -> None:
    r = client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", CSV_VIDE.encode(), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_import_csv_invalide_retourne_400(client: TestClient) -> None:
    csv_sans_colonne = "Titre,Nombre\nIdée A,10\n"
    r = client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", csv_sans_colonne.encode(), "text/csv")},
    )
    assert r.status_code == 400
    assert "CSV invalide" in r.json()["detail"]


def test_lister_apres_import(client: TestClient) -> None:
    client.post(
        "/api/idees/import",
        data=FORMULAIRE,
        files={"fichier": ("export.csv", CSV_SIMPLE.encode(), "text/csv")},
    )
    r = client.get("/api/idees?produit_id=1")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.json()[0]["nb_votes"] >= r.json()[1]["nb_votes"]
