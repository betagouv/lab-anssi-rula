import pytest
from fastapi.testclient import TestClient

from api.idees import fabrique_depot_idees, fabrique_service_idees
from api.produits import fabrique_depot_produits
from api.projets import fabrique_depot_projets
from api.retours_bizdev import fabrique_depot_retours_bizdev
from api.retours_bizdev import fabrique_service_retours_bizdev
from infra.memoire.depot_idees import DepotIdeesMemoire
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_retours_bizdev import DepotRetoursBizDevMemoire
from retours_bizdev.service import ServiceRetoursBizDev
from idees.service import ServiceIdees
from projets.service import ProjetDejaExistant
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.projets.depot_projets_de_test import DepotProjetsDeTest
from serveur import app

CSV_BIZDEV = (
    "Verbatim,User nom,Rôle du user,Type cible,Source,Lien,Date,Qui ?,Catégorie,Item\n"
    "Retour A,Alice,RSSI,,,,01/01/24,Bob,[CAT],Item A\n"
)
CSV_FEATUREBASE = (
    "Title,Content,Upvote Count,Date\nIdée A,Description A,10,2024-01-01\n"
)


class DepotProjetEnConflit(DepotProjetsDeTest):
    def ajouter(self, produit_id: int, nom: str, brief: str):
        raise ProjetDejaExistant


class ServiceImportEnErreur(ServiceRetoursBizDev):
    def importer(self, produit_id: int, contenu_csv: str, projet_id: int | None = None):
        raise RuntimeError("erreur d'import")


@pytest.fixture
def contexte_sources():
    produits = DepotProduitsMemoire()
    produits.ajouter("MQC")
    produits.ajouter("MSC")
    projets = DepotProjetsDeTest()
    idees = DepotIdeesMemoire()
    retours = DepotRetoursBizDevMemoire()
    validation_albert = AdaptateurAlbertDeTest().avec_reponse(
        '{"valide":true,"problemes":[]}'
    )
    app.dependency_overrides[fabrique_depot_produits] = lambda: produits
    app.dependency_overrides[fabrique_depot_projets] = lambda: projets
    app.dependency_overrides[fabrique_depot_idees] = lambda: idees
    app.dependency_overrides[fabrique_depot_retours_bizdev] = lambda: retours
    app.dependency_overrides[fabrique_service_idees] = lambda: ServiceIdees(idees)
    app.dependency_overrides[fabrique_service_retours_bizdev] = lambda: (
        ServiceRetoursBizDev(retours)
    )
    yield TestClient(app), produits, projets, validation_albert
    app.dependency_overrides.clear()


def test_import_bizdev_est_isole_par_projet(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    premier = projets.ajouter(1, "Recherche A", "")
    second = projets.ajouter(1, "Recherche B", "")
    for projet, contenu in ((premier, CSV_BIZDEV), (second, CSV_BIZDEV)):
        reponse = client.post(
            "/api/produits/1/sources/bizdev",
            data={"projet_id": str(projet.id)},
            files={"fichier": ("retours.csv", contenu.encode(), "text/csv")},
        )
        assert reponse.status_code == 200
    remplacement = client.post(
        "/api/produits/1/sources/bizdev",
        data={"projet_id": str(second.id)},
        files={
            "fichier": (
                "retours.csv",
                CSV_BIZDEV.replace("Retour A", "Retour B").encode(),
                "text/csv",
            )
        },
    )
    assert remplacement.status_code == 200
    assert len(client.get(f"/api/retours-bizdev?projet_id={premier.id}").json()) == 1
    assert (
        client.get(f"/api/retours-bizdev?projet_id={second.id}").json()[0]["verbatim"]
        == "Retour B"
    )


def test_import_bizdev_sans_projet_est_scopé_produit(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data={"produit_seul": "true"},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 200
    assert reponse.json()["produit_id"] == 1
    assert reponse.json()["sources"][0]["projet_id"] is None
    assert projets.lister(1) == []


def test_import_featurebase_sans_projet_est_scopé_produit(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/1/sources/featurebase",
        data={"produit_seul": "true"},
        files={"fichier": ("idees.csv", CSV_FEATUREBASE.encode(), "text/csv")},
    )
    assert reponse.status_code == 200
    assert reponse.json()["sources"][0]["projet_id"] is None
    assert projets.lister(1) == []


def test_import_produit_refuse_csv_invalide_et_produit_inconnu(contexte_sources) -> None:
    client, _, _, _ = contexte_sources
    assert client.post(
        "/api/produits/1/sources/featurebase",
        data={"produit_seul": "true"},
        files={"fichier": ("idees.csv", b"Titre,Nombre\nA,1\n", "text/csv")},
    ).status_code == 400
    assert client.post(
        "/api/produits/99/sources/bizdev",
        data={"produit_seul": "true"},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    ).status_code == 404
def test_import_featurebase_cree_un_projet(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/1/sources/featurebase",
        data={
            "nouveau_projet_nom": "Nouveau projet",
            "nouveau_projet_brief": "Brief",
        },
        files={"fichier": ("idees.csv", CSV_FEATUREBASE.encode(), "text/csv")},
    )
    assert reponse.status_code == 200
    assert reponse.json()["projet"]["nom"] == "Nouveau projet"
    assert reponse.json()["sources"][0]["projet_id"] == 1
    assert projets.lister(1)[0].brief == "Brief"


def test_import_refuse_un_projet_d_un_autre_produit(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    projet = projets.ajouter(2, "Autre produit", "")
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data={"projet_id": str(projet.id)},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 404


def test_import_invalide_ne_cree_pas_de_projet(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/1/sources/featurebase",
        data={
            "nouveau_projet_nom": "Projet invalide",
        },
        files={"fichier": ("idees.csv", b"Titre,Nombre\nA,1\n", "text/csv")},
    )
    assert reponse.status_code == 400
    assert projets.lister(1) == []


def test_import_ne_consulte_pas_albert(contexte_sources) -> None:
    client, _, projets, albert = contexte_sources
    albert.avec_erreur(RuntimeError("Albert indisponible"))
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data={
            "nouveau_projet_nom": "Projet refusé",
        },
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 200
    assert projets.lister(1)[0].nom == "Projet refusé"


def test_import_refuse_produit_inconnu(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/99/sources/bizdev",
        data={"nouveau_projet_nom": "Projet"},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 404
    assert projets.lister(1) == []


@pytest.mark.parametrize(
    ("data", "statut"),
    [
        ({}, 200),
        (
            {
                "projet_id": "1",
                "nouveau_projet_nom": "Projet",
            },
            422,
        ),
        ({"nouveau_projet_nom": "   "}, 422),
    ],
)
def test_import_refuse_selection_projet(contexte_sources, data, statut) -> None:
    client, _, projets, _ = contexte_sources
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data=data,
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == statut
    assert projets.lister(1) == []


def test_import_refuse_nom_deja_utilise(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    projets.ajouter(1, "Projet", "")
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data={"nouveau_projet_nom": " projet "},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 409
    assert len(projets.lister(1)) == 1


def test_import_refuse_conflit_de_creation(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    app.dependency_overrides[fabrique_depot_projets] = DepotProjetEnConflit
    reponse = client.post(
        "/api/produits/1/sources/bizdev",
        data={"nouveau_projet_nom": "Projet"},
        files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
    )
    assert reponse.status_code == 409
    assert projets.lister(1) == []


def test_import_en_erreur_supprime_le_nouveau_projet(contexte_sources) -> None:
    client, _, projets, _ = contexte_sources
    app.dependency_overrides[fabrique_service_retours_bizdev] = lambda: (
        ServiceImportEnErreur(DepotRetoursBizDevMemoire())
    )
    with pytest.raises(RuntimeError, match="erreur d'import"):
        client.post(
            "/api/produits/1/sources/bizdev",
            data={"nouveau_projet_nom": "Projet"},
            files={"fichier": ("retours.csv", CSV_BIZDEV.encode(), "text/csv")},
        )
    assert projets.lister(1) == []
