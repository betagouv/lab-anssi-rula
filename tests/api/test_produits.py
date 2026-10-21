from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.produits import fabrique_depot_produits, routeur
from infra.memoire.depot_produits import DepotProduitsMemoire


def test_liste_uniquement_mss_msc() -> None:
    depot = DepotProduitsMemoire()
    depot.ajouter("MSS")
    depot.ajouter("MSC")
    depot.ajouter("hors_perimetre")
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    application.dependency_overrides[fabrique_depot_produits] = lambda: depot
    reponse = TestClient(application).get("/api/produits")
    assert reponse.status_code == 200
    assert [produit["nom"] for produit in reponse.json()] == ["MSS", "MSC"]
