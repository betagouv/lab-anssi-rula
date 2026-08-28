from datetime import datetime

from fastapi.testclient import TestClient
import pytest

from api.analyse_transverse import _groupes, fabrique_service_besoins
from besoins.depot import BesoinDetecte
from correspondance.depot import Cluster, Membre
from serveur import app


def test_analyse_transverse_est_scopée_par_produit(client: TestClient) -> None:
    produit = client.post("/api/produits", json={"nom": "Produit transverse"}).json()
    identifiant = produit["id"]

    assert client.get(f"/api/produits/{identifiant}/analyse-transverse").json() == {
        "besoins": [],
        "correspondances": [],
        "groupes": [],
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


def test_analyse_transverse_restaure_les_besoins_si_une_source_echoue(
    client: TestClient,
) -> None:
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


def test_groupes_transverses_conservent_les_verbatims_et_ajoutent_les_unitaires() -> (
    None
):
    date = datetime(2026, 1, 1)
    besoins = [
        BesoinDetecte(
            1,
            "transcript",
            12,
            "passage original",
            "Exporter",
            "verbatim transcript",
            12,
            "extrait",
            date,
            1,
            1,
        ),
        BesoinDetecte(
            2,
            "idee",
            4,
            "ligne FeatureBase",
            "Exporter",
            None,
            None,
            "extrait",
            date,
            1,
            None,
        ),
        BesoinDetecte(
            3,
            "retour_bizdev",
            8,
            "ligne BizDev",
            "Exporter",
            "verbatim BizDev",
            None,
            "extrait",
            date,
            1,
            None,
        ),
        BesoinDetecte(
            4,
            "transcript",
            13,
            "besoin seul",
            "Besoin seul",
            None,
            13,
            "extrait",
            date,
            1,
            1,
        ),
    ]
    clusters = [
        Cluster(
            "Exporter les données",
            3,
            [
                Membre("transcript", "Exporter", 12, "verbatim transcript", 12),
                Membre("idee", "Exporter", None, None, 4),
                Membre("retour_bizdev", "Exporter", None, "verbatim BizDev", 8),
            ],
        )
    ]

    groupes = _groupes(besoins, clusters)

    assert groupes == [
        {
            "nom_generique": "Exporter les données",
            "occurrences": 3,
            "passages": [
                {
                    "source": "transcript",
                    "source_id": 12,
                    "transcript_id": 12,
                    "projet_id": 1,
                    "texte_normalise": "Exporter",
                    "verbatim": "verbatim transcript",
                },
                {
                    "source": "idee",
                    "source_id": 4,
                    "transcript_id": None,
                    "projet_id": None,
                    "texte_normalise": "Exporter",
                    "verbatim": "ligne FeatureBase",
                },
                {
                    "source": "retour_bizdev",
                    "source_id": 8,
                    "transcript_id": None,
                    "projet_id": None,
                    "texte_normalise": "Exporter",
                    "verbatim": "verbatim BizDev",
                },
            ],
        },
        {
            "nom_generique": "Besoin seul",
            "occurrences": 1,
            "passages": [
                {
                    "source": "transcript",
                    "source_id": 13,
                    "transcript_id": 13,
                    "projet_id": 1,
                    "texte_normalise": "Besoin seul",
                    "verbatim": "besoin seul",
                }
            ],
        },
    ]
