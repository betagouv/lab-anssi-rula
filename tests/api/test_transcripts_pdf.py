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
    _occurrence_dict,
    _executer_job,
    fabrique_depot_transcripts_pdf,
    fabrique_executeur,
    fabrique_service_preparation_pdf,
    fabrique_service_analyse_pdf,
    fabrique_service_transcripts_pdf,
    fabrique_service_transcripts_pdf_travail,
    fabrique_executeur_preparation,
    reprendre_jobs,
    surveille_jobs,
    routeur,
)
from adaptateurs.exceptions import DelaiAlbertDepasse, ReponseAlbertInvalide
from infra.memoire.depot_transcripts_pdf import DepotTranscriptsPdfMemoire
from tests.adaptateurs.albert_de_test import AdaptateurAlbertDeTest
from tests.test_transcripts_pdf import _pdf, _reponses_preparation
from transcripts_pdf.analyse import ServiceAnalysePdf
from transcripts_pdf.depot import SourceTranscriptPdf
from transcripts_pdf.orchestration import ServiceTranscriptsPdf
from transcripts_pdf.service import (
    Locuteur,
    OccurrencePseudonymisation,
    ServicePreparationTranscript,
)


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
    reponse_analyse: str | None,
) -> tuple[TestClient, DepotTranscriptsPdfMemoire, FastAPI]:
    depot = DepotTranscriptsPdfMemoire()
    albert = AdaptateurAlbertDeTest()
    if reponse_analyse is None:
        albert.avec_erreur(AssertionError("Analyse non demandée."))
    else:
        albert.avec_reponse(reponse_analyse)
    service = ServiceTranscriptsPdf(
        depot,
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


def test_confirme_un_nom_de_reunion_avec_doubles_tirets() -> None:
    client, depot, _ = _client(None)
    body = _payload()
    body["nom_source"] = "reunion--zxe-akot-ibw--du-2026-09-30-a-10-09.pdf"

    reponse = client.post("/api/transcripts-pdf", json=body)

    assert reponse.status_code == 201
    assert depot.sources[0].nom_source == body["nom_source"]


def test_refuse_un_nom_source_invalide() -> None:
    client, _, _ = _client('{"valide": true, "problemes": []}')
    body = _payload()
    body["nom_source"] = "nom-personnel.pdf"

    assert client.post("/api/transcripts-pdf", json=body).status_code == 422


def test_confirme_apres_validation_humaine_sans_appel_albert_ni_analyse() -> None:
    client, depot, _ = _client(None)
    body = _payload()
    body["contenu"] = "SPEAKER_01: Contenu validé par la personne."

    reponse = client.post("/api/transcripts-pdf", json=body)

    assert reponse.status_code == 201
    assert depot.sources[0].contenu == body["contenu"]
    assert depot.obtenir_analyse(1) is None
    assert depot.jobs == []


def test_confirme_la_projection_fusionnee_sans_transmettre_les_occurrences() -> None:
    texte = "Locutrr_01: Pierre; Pierre Leroy; Leroy Dupont; Pierre Leroy Dupont"
    contexte = "Pierre Leroy Dupont et Pierre"
    preparation = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(
            _reponses_preparation(
                texte,
                contexte,
                detections=[
                    ("transcript", "Pierre", "identite"),
                    ("transcript", "Pierre Leroy", "identite"),
                    ("transcript", "Leroy Dupont", "organisation"),
                ],
            )
        ),
        "prompt",
    ).preparer("reunion.pdf", _pdf(texte), "bizdev", contexte)
    client, depot, _ = _client(None)
    body = _payload()
    body["contenu"] = preparation.contenu
    body["contexte"] = preparation.contexte
    body["locuteurs"] = [locuteur._asdict() for locuteur in preparation.locuteurs]

    reponse = client.post("/api/transcripts-pdf", json=body)

    assert reponse.status_code == 201
    assert depot.sources[0].contenu == preparation.contenu
    assert depot.sources[0].contexte == preparation.contexte
    assert "occurrences" not in body
    assert "contenu_original" not in body
    assert "Pierre" not in depot.sources[0].contenu + depot.sources[0].contexte


def test_modification_apres_validation_humaine_sans_appel_albert() -> None:
    client, depot, _ = _client(None)
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
    body["contenu"] = "SPEAKER_01: Contenu corrigé et validé par la personne."
    reponse = client.put(f"/api/transcripts-pdf/{source.id}", json=body)

    assert reponse.status_code == 200
    assert depot.sources[0].contenu == body["contenu"]
    assert depot.obtenir_analyse(source.id) is None
    assert depot.jobs == []


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
    albert = AdaptateurAlbertDeTest().avec_erreur(
        AssertionError("Analyse non demandée.")
    )
    app.dependency_overrides[fabrique_service_transcripts_pdf] = lambda: (
        ServiceModificationRaceDeTest(
            depot,
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
    depot.fonctionnalites.append({"transcript_id": source.id, "contenu": "Besoin"})

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
    assert depot.obtenir(source.id) is None
    assert depot.obtenir_analyse(source.id) is None
    assert depot.fonctionnalites == []


def test_occurrence_api_convertit_les_offsets_python_en_utf16() -> None:
    occurrence = OccurrencePseudonymisation(
        "1", "Alice", 2, 7, "transcript", "identite", "[IDENTITE_01]"
    )

    resultat = _occurrence_dict(occurrence, "😀 Alice", "")

    assert resultat["debut"] == 3
    assert resultat["fin"] == 8


def test_preparation_pdf_et_erreurs_de_traitement(caplog) -> None:
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
    assert resultat.json()["contenu_original"] == "Bonjour"
    assert resultat.json()["contexte_original"] == ""
    assert resultat.headers["cache-control"] == "no-store"
    assert resultat.json()["occurrences"] == []
    assert resultat.json()["conflits_categories_fusionnes"] == 0
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
    caplog.set_level(logging.ERROR, logger="api.transcripts_pdf")
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
    assert "Échec préparation transcript PDF" in caplog.text
    assert "exception_type=ValueError" in caplog.text
    assert "phase=anonymisation" in caplog.text
    assert "jeton_hash=" in caplog.text
    assert "Albert indisponible" not in caplog.text
    assert jeton_echec not in caplog.text
    delai_albert = DelaiAlbertDepasse("contenu prive")
    delai_albert.diagnostic.update(
        groupe=7,
        delai_tentative_s=180,
        duree_tentative_s=180.001,
        duree_totale_s=180.001,
        tentatives=1,
    )
    albert.avec_erreur(delai_albert)
    delai = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={"fichier": ("reunion.pdf", fichier, "application/pdf")},
    )
    jeton_delai = delai.json()["jeton"]
    resultat_delai = client.get(f"/api/transcripts-pdf/preparation/{jeton_delai}")
    for _ in range(100):
        if resultat_delai.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat_delai = client.get(f"/api/transcripts-pdf/preparation/{jeton_delai}")
    assert resultat_delai.json()["erreur"] == (
        "L'API Albert n'a pas répondu dans le délai imparti."
    )
    assert "exception_type=DelaiAlbertDepasse" in caplog.text
    assert "code=delai_albert_depasse" in caplog.text
    assert (
        "message=\"L'API Albert n'a pas répondu dans le délai imparti.\"" in caplog.text
    )
    assert "groupe=1" in caplog.text
    assert "delai_tentative_s=180" in caplog.text
    assert "duree_tentative_s=180.001" in caplog.text
    assert "contenu prive" not in caplog.text


def test_preparation_api_expose_une_fusion_temporaire_sans_persister() -> None:
    client, depot, app = _client('{"valide": true, "problemes": []}')
    texte = "Speaker_01: Alice"
    service = ServicePreparationTranscript(
        AdaptateurAlbertDeTest().avec_reponses(
            _reponses_preparation(
                texte,
                detections=[
                    ("transcript", "Alice", "identite"),
                    ("transcript", "Alice", "organisation"),
                ],
            )
        ),
        "prompt",
    )
    app.dependency_overrides[fabrique_service_preparation_pdf] = lambda: service

    soumission = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={"fichier": ("reunion.pdf", _pdf(texte), "application/pdf")},
    )
    jeton = soumission.json()["jeton"]
    resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")
    for _ in range(100):
        if resultat.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")

    assert resultat.json()["statut"] == "termine"
    assert resultat.json()["conflits_categories_fusionnes"] == 1
    assert resultat.json()["contenu"] == "SPEAKER_01: [DONNEE_SENSIBLE_01]"
    assert depot.sources == []


def test_preparation_api_explique_une_erreur_de_validation_sans_detail_prive() -> None:
    client, _, app = _client('{"valide": true, "problemes": []}')
    app.dependency_overrides[fabrique_service_preparation_pdf] = lambda: (
        ServicePreparationTranscript(
            AdaptateurAlbertDeTest().avec_reponse("pas-json"), "prompt"
        )
    )

    soumission = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={
            "fichier": ("reunion.pdf", _pdf("Speaker_01: Alice"), "application/pdf")
        },
    )
    jeton = soumission.json()["jeton"]
    resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")
    for _ in range(100):
        if resultat.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")

    assert resultat.json()["statut"] == "echec"
    assert resultat.json()["erreur"] == (
        "Une réponse d’anonymisation incomplète ou incohérente a empêché de "
        "produire un brouillon fiable. "
        "Réessayez l’import ; si le problème persiste, contactez le support."
    )


def test_preparation_api_explique_une_reponse_albert_invalide() -> None:
    client, _, app = _client('{"valide": true, "problemes": []}')
    app.dependency_overrides[fabrique_service_preparation_pdf] = lambda: (
        ServicePreparationTranscript(
            AdaptateurAlbertDeTest().avec_erreur(ReponseAlbertInvalide()), "prompt"
        )
    )

    soumission = client.post(
        "/api/transcripts-pdf/preparation",
        data={"type_source": "bizdev"},
        files={
            "fichier": ("reunion.pdf", _pdf("Speaker_01: Alice"), "application/pdf")
        },
    )
    jeton = soumission.json()["jeton"]
    resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")
    for _ in range(100):
        if resultat.json()["statut"] != "en_cours":
            break
        time.sleep(0.01)
        resultat = client.get(f"/api/transcripts-pdf/preparation/{jeton}")

    assert resultat.json()["statut"] == "echec"
    assert resultat.json()["erreur"] == (
        "Une réponse d’anonymisation incomplète ou incohérente a empêché de "
        "produire un brouillon fiable. "
        "Réessayez l’import ; si le problème persiste, contactez le support."
    )


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
    analyseur = ServiceAnalysePdf(
        AdaptateurAlbertDeTest(), {"produit": "prompt", "bizdev": "prompt"}
    )
    assert (
        fabrique_service_preparation_pdf().__class__.__name__
        == "ServicePreparationTranscript"
    )
    assert fabrique_service_analyse_pdf().__class__.__name__ == "ServiceAnalysePdf"
    service_travail = fabrique_service_transcripts_pdf_travail()
    assert service_travail._depot.__class__.__name__ == "DepotTranscriptsPdfPostgres"
    assert service_travail._analyseur.__class__.__name__ == "ServiceAnalysePdf"
    assert fabrique_executeur() is not None
    assert (
        fabrique_service_transcripts_pdf(depot, analyseur).__class__.__name__
        == "ServiceTranscriptsPdf"
    )
    service = ServiceTranscriptsPdf(depot, analyseur)
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
