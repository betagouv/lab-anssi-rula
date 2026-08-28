import pytest
from fastapi.testclient import TestClient

from api.projets import (
    fabrique_depot_projets,
    fabrique_service_scan,
    fabrique_service_validation,
)
from api.produits import fabrique_depot_produits
from projets.service import ServiceScansProjets
from projets.service import ProjetDejaExistant
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest
from infra.memoire.depot_produits import DepotProduitsMemoire
from validation_transcript.service import ServiceValidationTranscript
from serveur import app


@pytest.fixture
def contexte_projets():
    def creer(depot=None, produits=None):
        depot = depot or DepotProjetsDeTest()
        albert_validation = AdaptateurAlbertDeTest().avec_reponse(
            '{"valide":true,"problemes":[]}'
        )
        validation = ServiceValidationTranscript(albert_validation, "prompt")
        scan = ServiceScansProjets(
            depot, AdaptateurAlbertDeTest().avec_reponse("Scan"), "prompt"
        )
        app.dependency_overrides[fabrique_depot_projets] = lambda: depot
        app.dependency_overrides[fabrique_service_validation] = lambda: validation
        app.dependency_overrides[fabrique_service_scan] = lambda: scan
        if produits:
            app.dependency_overrides[fabrique_depot_produits] = lambda: produits
        return TestClient(app), depot, albert_validation

    yield creer
    app.dependency_overrides.clear()


def entretien_payload() -> dict:
    return {
        "participant": "A",
        "date_entretien": "2026-08-25",
        "moderateur": "B",
        "contenu": "Texte",
        "note_moderateur": "",
    }


def test_parcours_projet(contexte_projets) -> None:
    client, _, albert_validation = contexte_projets()
    assert client.get("/api/projets?produit_id=1").json() == []
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 1, "nom": "Projet", "confirmation": False},
        ).status_code
        == 201
    )
    assert client.get("/api/projets/1").json()["nom"] == "Projet"
    assert client.get("/api/projets/2").status_code == 404
    assert (
        client.post(
            "/api/projets/1/entretiens",
            json={**entretien_payload(), "confirmation": False},
        ).status_code
        == 422
    )
    albert_validation.avec_reponse(
        '{"valide":false,"problemes":[{"categorie":"technologie_ou_produit","element":"outil","raison":"Produit identifiable."}]}'
    )
    reponse = client.post(
        "/api/projets/1/entretiens",
        json={**entretien_payload(), "confirmation": True},
    )
    assert reponse.status_code == 422
    assert reponse.json()["detail"]["raisons"][0]["element"] == "outil"
    albert_validation.avec_reponse('{"valide":true,"problemes":[]}')
    assert (
        client.post(
            "/api/projets/1/entretiens",
            json={**entretien_payload(), "confirmation": True},
        ).status_code
        == 201
    )
    assert len(client.get("/api/projets/1/entretiens").json()) == 1
    assert (
        client.post(
            "/api/projets/2/entretiens",
            json={**entretien_payload(), "confirmation": True},
        ).status_code
        == 404
    )
    assert client.get("/api/projets/1/scan").status_code == 404
    assert client.post("/api/projets/1/scan").json()["brouillon"] == "Scan"
    assert client.get("/api/projets/1/scan").json()["brouillon"] == "Scan"
    assert client.post("/api/projets/2/scan").status_code == 404
    assert (
        client.put("/api/projets/1/scan", json={"contenu": "Corrigé"}).json()[
            "brouillon"
        ]
        == "Corrigé"
    )
    assert (
        client.put("/api/projets/2/scan", json={"contenu": "Corrigé"}).status_code
        == 404
    )
    assert client.post("/api/projets/1/scan/validation").json()["valide"] == "Corrigé"
    assert client.post("/api/projets/2/scan/validation").status_code == 404


def test_creer_projet_sans_confirmation(contexte_projets) -> None:
    client, _, _ = contexte_projets()
    assert (
        client.post(
            "/api/projets", json={"produit_id": 1, "nom": "Projet sans confirmation"}
        ).status_code
        == 201
    )


def test_ajouter_source_reutilise_un_projet_et_reste_atomique(contexte_projets) -> None:
    produits = DepotProduitsMemoire()
    produits.ajouter("MQC")
    produits.ajouter("MSC")
    client, _, albert_validation = contexte_projets(produits=produits)
    entretien = entretien_payload()
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 1, "nom": "Recherche", "confirmation": True},
        ).status_code
        == 201
    )
    source = client.post(
        "/api/produits/1/sources",
        json={"projet_id": 1, "entretien": entretien, "confirmation": True},
    )
    assert source.status_code == 201
    second = client.post(
        "/api/produits/1/sources",
        json={"projet_id": 1, "entretien": entretien, "confirmation": True},
    )
    assert second.status_code == 201
    assert albert_validation.messages_recus[-1][-1]["content"] == "Texte"
    assert len(client.get("/api/projets?produit_id=1").json()) == 1
    assert len(client.get("/api/projets/1/entretiens").json()) == 2
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 1, "nom": " recherche ", "confirmation": True},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 1, "nom": "   ", "confirmation": True},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 2, "nom": "Recherche", "confirmation": True},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/produits/2/sources",
            json={"projet_id": 1, "entretien": entretien, "confirmation": True},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/produits/99/sources",
            json={"projet_id": 1, "entretien": entretien, "confirmation": True},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/produits/1/sources",
            json={
                "projet_id": 1,
                "nouveau_projet": {"nom": "Autre"},
                "entretien": entretien,
                "confirmation": True,
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/produits/1/sources",
            json={
                "nouveau_projet": {"nom": "Recherche"},
                "entretien": entretien,
                "confirmation": True,
            },
        ).status_code
        == 409
    )
    albert_validation.avec_reponse(
        '{"valide":false,"problemes":[{"categorie":"identite","element":"A","raison":"Identité."}]}'
    )
    refus = client.post(
        "/api/produits/1/sources",
        json={
            "nouveau_projet": {"nom": "Nouveau", "brief": "Brief"},
            "entretien": entretien,
            "confirmation": True,
        },
    )
    assert refus.status_code == 422
    assert len(client.get("/api/projets?produit_id=1").json()) == 1


class _DepotProjetConflit(DepotProjetsDeTest):
    def ajouter(self, produit_id: int, nom: str, brief: str):
        raise ProjetDejaExistant

    def ajouter_source(self, *args, **kwargs):
        raise ProjetDejaExistant


def test_conflit_de_nom_concurrent_est_retourne(contexte_projets) -> None:
    depot = _DepotProjetConflit()
    produits = DepotProduitsMemoire()
    produits.ajouter("MQC")
    client, _, _ = contexte_projets(depot=depot, produits=produits)
    assert (
        client.post(
            "/api/projets",
            json={"produit_id": 1, "nom": "Projet", "confirmation": True},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/produits/1/sources",
            json={
                "nouveau_projet": {"nom": "Projet"},
                "entretien": entretien_payload(),
                "confirmation": True,
            },
        ).status_code
        == 409
    )
