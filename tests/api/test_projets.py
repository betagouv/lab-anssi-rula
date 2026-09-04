from datetime import date

import pytest
from fastapi.testclient import TestClient

from adaptateurs.exceptions import ErreurCommunicationAlbert
from api.projets import (
    _erreur_analyse,
    fabrique_depot_projets,
    fabrique_depot_analyse,
    fabrique_service_analyse_projet,
    fabrique_service_scan,
    fabrique_service_validation,
)
from api.produits import fabrique_depot_produits
from projets.service import ServiceScansProjets
from projets.service import ProjetDejaExistant
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_analyse import DepotAnalyseMemoire
from projets.analyse import ServiceAnalyseProjet
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
    entretien = client.get("/api/projets/1/entretiens/1")
    assert entretien.status_code == 200
    assert entretien.json()["contenu"] == "Texte"
    assert client.get("/api/projets/2/entretiens/1").status_code == 404
    assert client.get("/api/projets/1/entretiens/99").status_code == 404
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


def test_refuse_un_entretien_incomplet_sans_appeler_albert(contexte_projets) -> None:
    client, depot, albert_validation = contexte_projets()
    projet = depot.ajouter(1, "Projet", "")

    reponse = client.post(
        f"/api/projets/{projet.id}/entretiens",
        json={"participant": " ", "date_entretien": "", "confirmation": True},
    )

    assert reponse.status_code == 422
    assert reponse.json() == {
        "detail": {
            "message": "Vérifiez les champs obligatoires avant de continuer.",
            "champs": [
                "Le renseignement concernant le prénom de l’utilisateur est obligatoire.",
                "La date de l’entretien est invalide.",
                "Le renseignement concernant le modérateur est obligatoire.",
                "Le renseignement concernant le transcript de l’entretien est obligatoire.",
            ],
        }
    }
    assert albert_validation.messages_recus == []
    assert depot.lister_entretiens(projet.id) == []


def test_refuse_les_champs_entretien_absents_explicitement(contexte_projets) -> None:
    client, depot, albert_validation = contexte_projets()
    projet = depot.ajouter(1, "Projet", "")

    reponse = client.post(
        f"/api/projets/{projet.id}/entretiens",
        json={},
    )

    assert reponse.status_code == 422
    assert "le prénom de l’utilisateur" in reponse.json()["detail"]["champs"][0]
    assert len(reponse.json()["detail"]["champs"]) == 5
    assert albert_validation.messages_recus == []
    assert depot.lister_entretiens(projet.id) == []


def test_refuse_un_entretien_source_incomplet_sans_appeler_albert(
    contexte_projets,
) -> None:
    produits = DepotProduitsMemoire()
    produits.ajouter("MQC")
    client, depot, albert_validation = contexte_projets(produits=produits)

    reponse = client.post(
        "/api/produits/1/sources",
        json={
            "projet_id": None,
            "nouveau_projet": {"nom": "Projet"},
            "entretien": {
                "participant": " ",
                "date_entretien": "2026-08-25",
                "moderateur": "Bob",
                "contenu": "Texte",
            },
            "confirmation": True,
        },
    )

    assert reponse.status_code == 422
    assert "le prénom de l’utilisateur" in reponse.json()["detail"]["champs"][0]
    assert albert_validation.messages_recus == []
    assert depot.lister(1) == []


def test_explicite_l_indisponibilite_d_albert_sans_persistance(
    contexte_projets,
) -> None:
    client, depot, albert_validation = contexte_projets()
    projet = depot.ajouter(1, "Projet", "")
    albert_validation.avec_erreur(ErreurCommunicationAlbert())

    reponse = client.post(
        f"/api/projets/{projet.id}/entretiens",
        json={**entretien_payload(), "confirmation": True},
    )

    assert reponse.status_code == 503
    assert reponse.json() == {
        "detail": "L'API Albert est indisponible. Réessayez dans quelques instants."
    }
    assert depot.lister_entretiens(projet.id) == []


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


def test_parcours_des_etapes_d_analyse() -> None:
    depot = DepotProjetsDeTest()
    projet = depot.ajouter(1, "Recherche", "Brief")
    depot.ajouter_entretien(projet.id, "A", date(2026, 8, 25), "B", "Transcript", "")
    analyse = DepotAnalyseMemoire()
    service = ServiceAnalyseProjet(
        depot, analyse, AdaptateurAlbertDeTest().avec_reponse("Résultat")
    )
    app.dependency_overrides[fabrique_depot_projets] = lambda: depot
    app.dependency_overrides[fabrique_depot_analyse] = lambda: analyse
    app.dependency_overrides[fabrique_service_analyse_projet] = lambda: service
    client = TestClient(app)
    try:
        configuration = client.get(f"/api/projets/{projet.id}/analyse/configuration")
        assert configuration.status_code == 200
        assert configuration.json()["blocs"][0]["cle"] == "role"
        assert len(configuration.json()["etapes"]) == 3
        assert (
            client.post(
                f"/api/projets/{projet.id}/analyse/etapes/points-a-retenir/generation"
            ).status_code
            == 409
        )
        scan = client.post(
            f"/api/projets/{projet.id}/analyse/etapes/scan-neutre/generation"
        )
        assert scan.status_code == 201
        assert (
            client.put(
                f"/api/projets/{projet.id}/analyse/etapes/scan-neutre",
                json={"contenu": "Corrigé"},
            ).json()["brouillon"]
            == "Corrigé"
        )
        assert (
            client.post(
                f"/api/projets/{projet.id}/analyse/etapes/scan-neutre/validation"
            ).json()["valide"]
            == "Corrigé"
        )
        assert (
            client.post(
                f"/api/projets/{projet.id}/analyse/etapes/points-a-retenir/generation"
            ).status_code
            == 201
        )
        assert (
            client.post(
                f"/api/projets/{projet.id}/analyse/etapes/points-a-retenir/validation"
            ).status_code
            == 200
        )
        assert client.get(f"/api/projets/{projet.id}/analyse/detail").json()["etapes"]
    finally:
        app.dependency_overrides.clear()


def test_erreurs_des_routes_d_analyse() -> None:
    depot = DepotProjetsDeTest()
    analyse = DepotAnalyseMemoire()
    service = ServiceAnalyseProjet(depot, analyse, AdaptateurAlbertDeTest())
    app.dependency_overrides[fabrique_depot_projets] = lambda: depot
    app.dependency_overrides[fabrique_depot_analyse] = lambda: analyse
    app.dependency_overrides[fabrique_service_analyse_projet] = lambda: service
    client = TestClient(app)
    try:
        for url in (
            "/api/projets/99/analyse/configuration",
            "/api/projets/99/analyse/etapes",
            "/api/projets/99/analyse/detail",
        ):
            assert client.get(url).status_code == 404
        assert (
            client.put(
                "/api/projets/99/analyse/configuration", json={"blocs": {}}
            ).status_code
            == 404
        )
        projet = depot.ajouter(1, "Configuration", "")
        assert (
            client.put(
                f"/api/projets/{projet.id}/analyse/configuration",
                json={"blocs": {"role": "Rôle"}},
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/projets/99/analyse/etapes/inconnue/generation"
            ).status_code
            == 404
        )
        assert (
            client.put(
                "/api/projets/99/analyse/etapes/inconnue", json={"contenu": "x"}
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/api/projets/99/analyse/etapes/inconnue/validation"
            ).status_code
            == 404
        )
        projet_sans_entretien = depot.ajouter(1, "Recherche", "")
        assert (
            client.post(
                f"/api/projets/{projet_sans_entretien.id}/analyse/etapes/scan-neutre/generation"
            ).status_code
            == 422
        )
        assert _erreur_analyse(ValueError("erreur")).status_code == 422
    finally:
        app.dependency_overrides.clear()
