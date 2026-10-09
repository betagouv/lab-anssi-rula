from fastapi import FastAPI
from fastapi.testclient import TestClient
from concurrent.futures import Executor, Future
import asyncio
import logging
import time
import api.transcripts_pdf as api_pdf
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, cast

from api.transcripts_pdf import (
    _executer_job,
    fabrique_depot_transcripts_pdf,
    fabrique_executeur,
    fabrique_service_preparation_pdf,
    fabrique_service_analyse_pdf,
    fabrique_service_validation_pdf,
    fabrique_service_transcripts_pdf,
    fabrique_service_transcripts_pdf_travail,
    fabrique_executeur_preparation,
    reprendre_jobs,
    surveille_jobs,
    routeur,
)
from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf
from transcripts_pdf.analyse import ServiceAnalysePdf
from transcripts_pdf.depot import SourceTranscriptPdf
from transcripts_pdf.orchestration import ServiceTranscriptsPdf
from transcripts_pdf.service import Locuteur, ServicePreparationTranscript
from validation_transcript.service import ServiceValidationTranscript


class ExecuteurDeTest(Executor):
    def __init__(self) -> None:
        self.taches: list[tuple[object, tuple[object, ...]]] = []

    def submit(self, fn, /, *args, **kwargs) -> Future:
        self.taches.append((fn, args))
        return Future()


class ServiceModificationRaceDeTest(ServiceTranscriptsPdf):
    def modifier(
        self,
        transcript_id: int,
        date_entretien: date | None,
        contenu: str,
        contexte: str,
        locuteurs: list[Locuteur],
    ) -> SourceTranscriptPdf | None:
        return None


class ServiceEchecWorkerDeTest(ServiceTranscriptsPdf):
    def executer_job(self, job_id: int) -> None:
        raise ValueError("texte sensible")


def _client(
    reponse_garde_fou: str,
) -> tuple[TestClient, DepotTranscriptsPdfMemoire, FastAPI]:
    depot = DepotTranscriptsPdfMemoire()
    albert = AdaptateurAlbertDeTest().avec_reponse(reponse_garde_fou)
    service = ServiceTranscriptsPdf(
        depot,
        ServiceValidationTranscript(albert, "prompt"),
        ServiceAnalysePdf(albert, {"produit": "prompt", "bizdev": "prompt"}),
    )
    app = FastAPI()
    app.include_router(routeur, prefix="/api")
    app.dependency_overrides[fabrique_service_transcripts_pdf] = lambda: service
    app.dependency_overrides[fabrique_executeur] = lambda: ExecuteurDeTest()
    app.dependency_overrides[fabrique_depot_transcripts_pdf] = lambda: depot
    return TestClient(app), depot, app


def _payload() -> dict[str, Any]:
    return {
        "type_source": "bizdev",
        "nom_source": "reunion-_zbq-okak-bsa_-du-2026-04-07-a-10_34.pdf",
        "produit_id": 1,
        "projet_id": None,
        "date_entretien": "2026-04-07",
        "contenu": "SPEAKER_01: Le service répond au besoin.",
        "contexte": "",
        "locuteurs": [
            {
                "identifiant": "SPEAKER_01",
                "role": "externe",
                "justification": "Participant externe.",
            }
        ],
    }


def test_confirme_et_liste_une_source_anonymisee() -> None:
    client, depot, _ = _client('{"valide": true, "problemes": []}')

    reponse = client.post("/api/transcripts-pdf", json=_payload())

    assert reponse.status_code == 201
    assert reponse.json()["nom_source"] == _payload()["nom_source"]
    assert client.get("/api/transcripts-pdf/produits/1").json()[0]["id"] == 1
    assert depot.sources[0].projet_id is None


def test_refuse_un_nom_source_invalide() -> None:
    client, _, _ = _client('{"valide": true, "problemes": []}')
    body = _payload()
    body["nom_source"] = "nom-personnel.pdf"

    assert client.post("/api/transcripts-pdf", json=body).status_code == 422


def test_garde_fou_retourne_les_elements_a_corriger() -> None:
    client, _, _ = _client(
        '{"valide": false, "problemes": [{"categorie": "identite", "element": "Nom test", "raison": "Remplacez ce nom."}]}'
    )

    reponse = client.post("/api/transcripts-pdf", json=_payload())

    assert reponse.status_code == 422
    assert reponse.json()["detail"]["problemes"][0]["raison"] == "Remplacez ce nom."


def test_modification_garde_fou_retourne_les_elements_a_corriger() -> None:
    client, depot, _ = _client(
        '{"valide": false, "problemes": [{"categorie": "secret", "element": "clé", "raison": "Retirez-la."}]}'
    )
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )

    reponse = client.put(f"/api/transcripts-pdf/{source.id}", json=_payload())

    assert reponse.status_code == 422
    assert reponse.json()["detail"]["problemes"][0]["raison"] == "Retirez-la."


def test_modification_rejette_date_absente() -> None:
    client, depot, _ = _client('{"valide": true, "problemes": []}')
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )
    body = _payload()
    body["date_entretien"] = None

    assert client.put(f"/api/transcripts-pdf/{source.id}", json=body).status_code == 422


def test_modification_retourne_404_si_la_source_disparait() -> None:
    client, depot, app = _client('{"valide": true, "problemes": []}')
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )
    albert = AdaptateurAlbertDeTest().avec_reponse('{"valide": true, "problemes": []}')
    app.dependency_overrides[fabrique_service_transcripts_pdf] = lambda: (
        ServiceModificationRaceDeTest(
            depot,
            ServiceValidationTranscript(albert, "prompt"),
            ServiceAnalysePdf(albert, {"produit": "prompt", "bizdev": "prompt"}),
        )
    )

    assert (
        client.put(f"/api/transcripts-pdf/{source.id}", json=_payload()).status_code
        == 404
    )


def test_analyse_refuse_une_source_absente() -> None:
    client, _, _ = _client('{"valide": true, "problemes": []}')

    assert client.post("/api/transcripts-pdf/999/analyse").status_code == 404


def test_lit_modifie_supprime_et_analyse_une_source() -> None:
    client, depot, _ = _client('{"valide": true, "problemes": []}')
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )
    job = depot.reclamer_job(depot.creer_job(source.id).id)
    assert job is not None
    assert depot.finaliser(job, {"resume": "Résumé."}, [], "pdf-v1", "bizdev-v1")

    assert client.get(f"/api/transcripts-pdf/{source.id}").status_code == 200
    assert client.get(f"/api/transcripts-pdf/{source.id}/job").status_code == 200
    body = _payload()
    body["contenu"] = "SPEAKER_01: Texte modifié."
    assert client.put(f"/api/transcripts-pdf/{source.id}", json=body).status_code == 200
    assert client.put("/api/transcripts-pdf/999", json=body).status_code == 404
    assert client.get(f"/api/transcripts-pdf/{source.id}/analyse").status_code == 200
    assert client.get(f"/api/transcripts-pdf/{source.id}/job").status_code == 404
    assert client.post(f"/api/transcripts-pdf/{source.id}/analyse").status_code == 202
    assert client.get(f"/api/transcripts-pdf/{source.id}/job").status_code == 200
    assert client.get("/api/transcripts-pdf/999").status_code == 404
    assert client.delete(f"/api/transcripts-pdf/{source.id}").status_code == 204
    assert client.delete(f"/api/transcripts-pdf/{source.id}").status_code == 404
    assert client.get(f"/api/transcripts-pdf/{source.id}/job").status_code == 404


def test_preparation_pdf_et_erreurs_de_traitement() -> None:
    client, _, app = _client('{"valide": true, "problemes": []}')
    albert = AdaptateurAlbertDeTest().avec_reponse(
        '{"remplacements": [], "locuteurs": []}'
    )
    preparation = ServicePreparationTranscript(albert, "prompt")
    app.dependency_overrides[fabrique_service_preparation_pdf] = lambda: preparation
    fichier = _pdf("Bonjour")

    reponse = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={"fichier": ("reunion.pdf", fichier, "application/pdf")},
    )
    assert reponse.status_code == 202
    jeton = reponse.json()["jeton"]
    resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")
    for _ in range(100):
        if resultat.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")
    assert resultat.json()["statut"] == "termine"
    assert resultat.json()["progression"]["phase"] == "termine"
    assert resultat.json()["progression"]["groupes_termines"] == 1
    assert resultat.json()["progression"]["groupes_total"] == 1
    assert resultat.json()["remplacements"] == []
    trop_long = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={
            "fichier": ("reunion.pdf", b"x" * (10 * 1024 * 1024 + 1), "application/pdf")
        },
    )
    assert trop_long.status_code == 202
    statut_trop_long = client.get(
        f"/api/transcripts-pdf/preparation/{trop_long.json()['jeton']}"
    )
    for _ in range(100):
        if statut_trop_long.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        statut_trop_long = client.get(
            f"/api/transcripts-pdf/preparation/{trop_long.json()['jeton']}"
        )
    assert statut_trop_long.json()["statut"] == "echec"
    assert statut_trop_long.json()["erreur"] == "Le fichier dépasse 10 Mo."
    assert statut_trop_long.json()["progression"]["phase"] == "echec"
    albert.avec_erreur(ValueError("Albert indisponible"))
    echec = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={"fichier": ("reunion.pdf", fichier, "application/pdf")},
    )
    assert echec.status_code == 202
    jeton_echec = echec.json()["jeton"]
    resultat_echec = client.get(f"/api/transcripts-pdf/preparation/{jeton_echec}")
    for _ in range(100):
        if resultat_echec.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat_echec = client.get(f"/api/transcripts-pdf/preparation/{jeton_echec}")
    assert resultat_echec.json()["statut"] == "echec"
    assert resultat_echec.json()["erreur"] == "La préparation du transcript a échoué."
    assert resultat_echec.json()["progression"]["phase"] == "echec"
    assert resultat_echec.json()["progression"]["groupes_termines"] == 0
    assert resultat_echec.json()["progression"]["groupes_en_cours"] == []


def test_progression_preparation_reste_liee_au_jeton() -> None:
    executeur = ExecuteurDeTest()
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponse('{"remplacements": [], "locuteurs": []}'),
        "prompt",
    )
    app = FastAPI()
    app.include_router(routeur, prefix="/api")
    app.dependency_overrides[fabrique_service_preparation_pdf] = lambda: service
    app.dependency_overrides[fabrique_executeur_preparation] = lambda: executeur
    client = TestClient(app)

    soumission = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={"fichier": ("reunion.pdf", _pdf("Bonjour"), "application/pdf")},
    ).json()

    assert soumission["progression"]["phase"] == "en_attente"
    assert soumission["progression"]["groupes_total"] is None
    fonction, arguments = executeur.taches[0]
    cast(Callable[..., object], fonction)(*arguments)
    resultat = client.get(
        f"/api/transcripts-pdf/preparation/{soumission['jeton']}"
    ).json()

    assert resultat["statut"] == "termine"
    assert resultat["progression"]["phase"] == "termine"
    assert resultat["progression"]["groupes_termines"] == 1
    assert resultat["progression"]["groupes_total"] == 1
    assert resultat["progression"]["duree_secondes"] >= 0


def test_factories_and_reprise_jobs() -> None:
    depot = DepotTranscriptsPdfMemoire()
    executeur = ExecuteurDeTest()
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )
    job = depot.creer_job(source.id)

    assert (
        fabrique_depot_transcripts_pdf().__class__.__name__
        == "DepotTranscriptsPdfPostgres"
    )
    reprendre_jobs(depot, executeur)
    assert executeur.taches == [(_executer_job, (job.id,))]
    garde_fou = ServiceValidationTranscript(AdaptateurAlbertDeTest(), "prompt")
    analyseur = ServiceAnalysePdf(
        AdaptateurAlbertDeTest(), {"produit": "prompt", "bizdev": "prompt"}
    )
    assert (
        fabrique_service_preparation_pdf().__class__.__name__
        == "ServicePreparationTranscript"
    )
    assert (
        fabrique_service_validation_pdf().__class__.__name__
        == "ServiceValidationTranscript"
    )
    assert fabrique_service_analyse_pdf().__class__.__name__ == "ServiceAnalysePdf"
    service_travail = fabrique_service_transcripts_pdf_travail()
    assert service_travail._depot.__class__.__name__ == "DepotTranscriptsPdfPostgres"
    assert (
        service_travail._garde_fou.__class__.__name__ == "ServiceValidationTranscript"
    )
    assert service_travail._analyseur.__class__.__name__ == "ServiceAnalysePdf"
    assert fabrique_executeur() is not None
    assert (
        fabrique_service_transcripts_pdf(depot, garde_fou, analyseur).__class__.__name__
        == "ServiceTranscriptsPdf"
    )
    service = ServiceTranscriptsPdf(depot, garde_fou, analyseur)
    _executer_job(job.id + 1, service)


def test_surveillance_reessaie_apres_expiration_du_delai() -> None:
    arreter = asyncio.Event()
    scans = 0

    def scanner() -> None:
        nonlocal scans
        scans += 1
        if scans == 2:
            arreter.set()

    asyncio.run(surveille_jobs(arreter, scanner, 0))

    assert scans == 2


def test_worker_journalise_le_type_sans_le_message_de_l_exception(caplog) -> None:
    _, depot, _ = _client('{"valide": true, "problemes": []}')
    service = ServiceEchecWorkerDeTest(
        depot,
        ServiceValidationTranscript(AdaptateurAlbertDeTest(), "prompt"),
        ServiceAnalysePdf(
            AdaptateurAlbertDeTest(), {"produit": "prompt", "bizdev": "prompt"}
        ),
    )
    caplog.set_level(logging.ERROR, logger=api_pdf.__name__)

    _executer_job(12, service)

    assert "exception_type=ValueError" in caplog.text
    assert "texte sensible" not in caplog.text


def test_surveillance_reprend_un_bail_expire_sans_action_utilisateur() -> None:
    depot = DepotTranscriptsPdfMemoire()
    executeur = ExecuteurDeTest()
    source = depot.ajouter(
        "bizdev",
        1,
        None,
        _payload()["nom_source"],
        date(2026, 4, 7),
        _payload()["contenu"],
        "",
        _payload()["locuteurs"],
    )
    job = depot.reclamer_job(depot.creer_job(source.id).id)
    assert job is not None
    arreter = asyncio.Event()
    scans = 0

    def scanner() -> None:
        nonlocal scans
        scans += 1
        reprendre_jobs(depot, executeur)
        if scans == 1:
            depot.jobs[0] = job._replace(
                bail_jusqua=datetime.now() + timedelta(seconds=60)
            )
        elif scans == 2:
            depot.jobs[0] = job._replace(
                bail_jusqua=datetime.now() - timedelta(seconds=1)
            )
        else:
            arreter.set()

    asyncio.run(surveille_jobs(arreter, scanner, 0))

    assert scans == 3
    assert executeur.taches == [(_executer_job, (job.id,))]


def test_preparation_expire_et_limite_les_demandes() -> None:
    client, _, _ = _client('"')
    futur = datetime.now(timezone.utc) + timedelta(minutes=2)
    api_pdf._PREPARATIONS["active-1"] = {"statut": "en_cours", "expire": futur}
    api_pdf._PREPARATIONS["active-2"] = {"statut": "en_cours", "expire": futur}
    assert client.get("/api/transcripts-pdf/preparation/inconnu").status_code == 404
    assert (
        client.post(
            "/api/transcripts-pdf/preparation",
            data={"type_source": "bizdev"},
            files={"fichier": ("reunion.pdf", _pdf("Bonjour"), "application/pdf")},
        ).status_code
        == 429
    )
    api_pdf._PREPARATIONS["running"] = {
        "statut": "en_cours",
        "expire": futur,
        "soumis_monotonic": time.monotonic(),
        "progression": {
            "phase": "en_attente",
            "groupes_termines": 0,
            "groupes_total": None,
            "groupes_en_cours": [],
        },
    }
    progression = client.get("/api/transcripts-pdf/preparation/running").json()
    assert progression["statut"] == "en_cours"
    assert progression["progression"]["phase"] == "en_attente"
    assert progression["progression"]["groupes_total"] is None
    assert progression["progression"]["duree_secondes"] >= 0
    api_pdf._PREPARATIONS["expired"] = {
        "statut": "termine",
        "expire": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    assert client.get("/api/transcripts-pdf/preparation/expired").status_code == 404
    api_pdf._PREPARATIONS.clear()
