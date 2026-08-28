from fastapi.testclient import TestClient
import pytest

from api.analyse_transverse import fabrique_service_besoins
from serveur import app


def test_analyse_transverse_est_scopée_par_produit(client: TestClient) -> None:
    produit = client.post("/api/produits", json={"nom": "Produit transverse"}).json()
    identifiant = produit["id"]

    assert client.get(f"/api/produits/{identifiant}/analyse-transverse").json() == {
        "besoins": [],
        "correspondances": [],
        "calcule_le": None,
    }
    resultat = client.post(f"/api/produits/{identifiant}/analyse-transverse")
    assert resultat.status_code == 200
    assert resultat.json()["besoins"] == []
    assert resultat.json()["correspondances"] == []
    assert resultat.json()["calcule_le"] is not None
    assert client.get(f"/api/produits/{identifiant}/besoins").json() == []


def test_analyse_transverse_refuse_un_produit_inconnu(client: TestClient) -> None:
    assert client.get("/api/produits/99/analyse-transverse").status_code == 404
    assert client.post("/api/produits/99/analyse-transverse").status_code == 404
    assert client.get("/api/produits/99/besoins").status_code == 404


def test_analyse_transverse_restaure_les_besoins_si_une_source_echoue(client: TestClient) -> None:
    produit = client.post("/api/produits", json={"nom": "Produit rollback"}).json()
    restaure = False

    class ServiceDeTest:
        def lister(self, **kwargs):
            return []

        def preparer(self, source, produit_id):
            if source == "idee":
                raise RuntimeError("Albert indisponible")
            return []

        def remplacer(self, source, besoins, produit_id):
            return []

        def restaurer(self, anciens, produit_id):
            nonlocal restaure
            restaure = True

    app.dependency_overrides[fabrique_service_besoins] = lambda: ServiceDeTest()
    try:
        with pytest.raises(RuntimeError):
            client.post(f"/api/produits/{produit['id']}/analyse-transverse")
    finally:
        app.dependency_overrides.pop(fabrique_service_besoins, None)
    assert restaure
