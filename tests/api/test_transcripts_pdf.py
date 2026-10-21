from collections.abc import Iterator
from concurrent.futures import Executor, Future
from datetime import date, datetime, timedelta, timezone
from typing import Callable, NamedTuple, TypeVar

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.produits import fabrique_depot_produits
from api.transcripts_pdf import (
    _PREPARATIONS,
    fabrique_executeur_preparation,
    fabrique_service_preparation_pdf,
    routeur,
)
from api.transcripts_pdf import fabrique_depot_transcripts_pdf
from infra.memoire.depot_produits import DepotProduitsMemoire
from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf, _reponses_preparation
from transcripts_pdf.service import ServicePreparationTranscript

_T = TypeVar("_T")
_ORIGINE = {"Origin": "https://testserver"}
_NOM_PDF = "reunion-_zbq-okak-bsa_-du-2026-04-07-a-10_34.pdf"
_TEXTE_SOURCE = "Locutrr_01: Alice veut exporter."


class ExecuteurSynchroneDeTest(Executor):
    def submit(
        self, fn: Callable[..., _T], /, *args: object, **kwargs: object
    ) -> Future[_T]:
        futur: Future[_T] = Future()
        try:
            futur.set_result(fn(*args, **kwargs))
        except BaseException as erreur:
            futur.set_exception(erreur)
        return futur


class ApiPdfDeTest(NamedTuple):
    client: TestClient
    application: FastAPI
    produits: DepotProduitsMemoire
    transcripts: DepotTranscriptsPdfMemoire


def _service_preparation(reponses: list[str]) -> ServicePreparationTranscript:
    return ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(reponses), "prompt de test"
    )


@pytest.fixture
def api_pdf_de_test() -> Iterator[ApiPdfDeTest]:
    _PREPARATIONS.clear()
    produits = DepotProduitsMemoire()
    produits.ajouter("MSS")
    produits.ajouter("MSC")
    produits.ajouter("MQC")
    transcripts = DepotTranscriptsPdfMemoire()
    service = _service_preparation(
        _reponses_preparation(
            _TEXTE_SOURCE,
            detections=[("transcript", "Alice", "identite")],
        )
        * 4
    )
    application = FastAPI()
    application.include_router(routeur, prefix="/api")
    application.dependency_overrides[fabrique_depot_produits] = lambda: produits
    application.dependency_overrides[fabrique_depot_transcripts_pdf] = lambda: (
        transcripts
    )
    application.dependency_overrides[fabrique_service_preparation_pdf] = lambda: service
    application.dependency_overrides[fabrique_executeur_preparation] = (
        ExecuteurSynchroneDeTest
    )
    with TestClient(application, base_url="https://testserver") as client:
        yield ApiPdfDeTest(client, application, produits, transcripts)
    _PREPARATIONS.clear()


def _preparer(
    client: TestClient, produit_id: int = 1, type_source: str = "produit"
) -> dict:
    reponse = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": type_source, "produit_id": str(produit_id)},
        files={"fichier": (_NOM_PDF, _pdf(_TEXTE_SOURCE), "application/pdf")},
        headers=_ORIGINE,
    )
    assert reponse.status_code == 202
    resultat = reponse.json()
    terminee = client.get(f"/api/transcripts-pdf/preparation/{resultat['identifiant']}")
    assert terminee.status_code == 200
    assert terminee.json()["statut"] == "termine"
    return {**terminee.json(), "identifiant": resultat["identifiant"]}


def _corps_confirmation(preparation: dict, contenu: str, produit_id: int) -> dict:
    return {
        "preparation_id": preparation["identifiant"],
        "type_source": preparation["type_source"],
        "nom_source": preparation["nom_source"],
        "produit_id": produit_id,
        "date_entretien": "2026-04-07",
        "contenu": contenu,
        "contexte": preparation["contexte"],
        "locuteurs": [
            {
                "identifiant": "SPEAKER_01",
                "role": "externe",
                "justification": "Le transcript le désigne comme participant.",
                "nom_affiche": "Intervenant 1",
            }
        ],
    }


def test_import_reprise_relecture_confirmation_historique_et_isolation(
    api_pdf_de_test: ApiPdfDeTest,
) -> None:
    client = api_pdf_de_test.client
    mss = _preparer(client)
    msc = _preparer(client, produit_id=2, type_source="bizdev")
    masque_id = "00000000-0000-4000-8000-000000000001"
    etat_relecture = {
        "masques": [
            {
                "identifiant": masque_id,
                "categorie": "secret",
                "valeur_anonyme": "[SECRET_01]",
                "actif": True,
            }
        ],
        "plages": [
            {
                "identifiant": "00000000-0000-4000-8000-000000000002",
                "masque_identifiant": masque_id,
                "champ": "transcript",
                "debut": 12,
                "fin": 17,
            }
        ],
        "selection": masque_id,
        "annulations": [],
        "retablissements": [],
    }
    mise_a_jour = client.put(
        f"/api/transcripts-pdf/preparation/{mss['identifiant']}/relecture",
        json={
            "etat_relecture": etat_relecture,
            "locuteurs": [
                {
                    "identifiant": "SPEAKER_01",
                    "role": "interne",
                    "nom_affiche": "Équipe produit",
                }
            ],
            "date_entretien": "2026-04-07",
        },
        headers=_ORIGINE,
    )
    assert mise_a_jour.status_code == 200
    reprise = client.get(
        f"/api/transcripts-pdf/preparation/{mss['identifiant']}"
    ).json()
    assert reprise["etat_relecture"] == etat_relecture
    assert reprise["locuteurs"][0]["nom_affiche"] == "Équipe produit"
    assert reprise["date_entretien"] == "2026-04-07"

    contenu_final = "SPEAKER_01: [SECRET_01] veut exporter."
    confirmation = client.post(
        "/api/transcripts-pdf",
        json=_corps_confirmation(mss, contenu_final, produit_id=1),
        headers=_ORIGINE,
    )
    assert confirmation.status_code == 201
    assert api_pdf_de_test.transcripts.sources[0].contenu == contenu_final
    confirmation_msc = client.post(
        "/api/transcripts-pdf",
        json=_corps_confirmation(
            msc, "SPEAKER_01: [IDENTITE_01] veut exporter.", produit_id=2
        ),
        headers=_ORIGINE,
    )
    assert confirmation_msc.status_code == 201

    historique_mss = client.get("/api/transcripts-pdf/produits/1")
    historique_msc = client.get("/api/transcripts-pdf/produits/2")
    assert [item["id"] for item in historique_mss.json()] == [1]
    assert [item["id"] for item in historique_msc.json()] == [2]
    assert client.get("/api/transcripts-pdf/1").json()["contenu"] == contenu_final
    assert client.get("/api/transcripts-pdf/2").json()["produit_id"] == 2
    assert msc["produit_id"] == 2

    modification = client.put(
        "/api/transcripts-pdf/1",
        json={
            "type_source": "produit",
            "nom_source": mss["nom_source"],
            "produit_id": 1,
            "date_entretien": "2026-04-08",
            "contenu": "SPEAKER_01: Version relue modifiée.",
            "contexte": "Contexte révisé",
            "locuteurs": [
                {
                    "identifiant": "SPEAKER_01",
                    "role": "interne",
                    "justification": "Participant interne.",
                    "nom_affiche": "Intervenant produit",
                }
            ],
        },
    )
    assert modification.status_code == 200
    assert modification.json()["date_entretien"] == "2026-04-08"
    assert (
        client.put(
            "/api/transcripts-pdf/1",
            json={**_corps_confirmation(mss, contenu_final, produit_id=2)},
        ).status_code
        == 404
    )
    assert client.delete("/api/transcripts-pdf/1").status_code == 204
    assert client.get("/api/transcripts-pdf/1").status_code == 404
    assert client.delete("/api/transcripts-pdf/2").status_code == 204
    assert client.get("/api/transcripts-pdf/2").status_code == 404


def test_import_refuse_origine_et_produit_invalides_et_expose_erreur_et_expiration(
    api_pdf_de_test: ApiPdfDeTest,
) -> None:
    client = api_pdf_de_test.client
    fichiers = {"fichier": (_NOM_PDF, _pdf(_TEXTE_SOURCE), "application/pdf")}
    donnees = {"type_source": "produit", "produit_id": "3"}
    assert (
        client.post(
            "/api/transcripts-pdf/preparation",
            data=donnees,
            files=fichiers,
            headers={"Origin": "https://different.test"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/transcripts-pdf/preparation",
            data=donnees,
            files=fichiers,
            headers=_ORIGINE,
        ).status_code
        == 422
    )

    service = _service_preparation(["{}"])
    api_pdf_de_test.application.dependency_overrides[
        fabrique_service_preparation_pdf
    ] = lambda: service
    reponse = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "produit", "produit_id": "1"},
        files={"fichier": (_NOM_PDF, _pdf(_TEXTE_SOURCE), "application/pdf")},
        headers=_ORIGINE,
    )
    identifiant = reponse.json()["identifiant"]
    erreur = client.get(f"/api/transcripts-pdf/preparation/{identifiant}")
    assert erreur.json()["statut"] == "echec"
    assert "incohérente" in erreur.json()["erreur"]

    api_pdf_de_test.application.dependency_overrides[
        fabrique_service_preparation_pdf
    ] = lambda: _service_preparation(
        _reponses_preparation(
            _TEXTE_SOURCE,
            detections=[("transcript", "Alice", "identite")],
        )
    )
    terminee = _preparer(client)
    _PREPARATIONS[terminee["identifiant"]]["expire"] = datetime.now(
        timezone.utc
    ) - timedelta(seconds=1)
    assert (
        client.get(
            f"/api/transcripts-pdf/preparation/{terminee['identifiant']}"
        ).status_code
        == 404
    )


def test_telechargement_et_liste_ne_doublent_pas_le_prefixe(
    api_pdf_de_test: ApiPdfDeTest,
) -> None:
    source = api_pdf_de_test.transcripts.ajouter(
        "bizdev",
        2,
        "pseudonymiser_pseudonymiser_reunion.pdf",
        date(2026, 4, 7),
        "SPEAKER_01: Transcript confirmé.",
        "Contexte confirmé",
        [{"identifiant": "SPEAKER_01", "role": "externe"}],
    )
    liste = api_pdf_de_test.client.get("/api/transcripts-pdf/produits/2")
    assert liste.json()[0]["nom_source"] == "pseudonymiser_reunion.pdf"
    telechargement = api_pdf_de_test.client.get(f"/api/transcripts-pdf/{source.id}/pdf")
    assert telechargement.status_code == 200
    assert telechargement.headers["content-type"] == "application/pdf"
    assert (
        'filename="pseudonymiser_reunion.pdf"'
        in telechargement.headers["content-disposition"]
    )
