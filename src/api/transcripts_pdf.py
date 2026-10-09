from concurrent.futures import Executor, ThreadPoolExecutor
import asyncio
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from adaptateurs.albert import AdaptateurAlbertReel
from configuration import charge_configuration
from infra.postgres.depot_transcripts_pdf import DepotTranscriptsPdfPostgres
from transcripts_pdf.analyse import ServiceAnalysePdf
from transcripts_pdf.depot import (
    AnalyseTranscriptPdf,
    DepotTranscriptsPdf,
    JobAnalyseTranscript,
    SourceTranscriptPdf,
)
from transcripts_pdf.extraction import ErreurPdf, TAILLE_MAXIMALE
from transcripts_pdf.orchestration import (
    ServiceTranscriptsPdf,
    SourcePdfInvalide,
    SourcePdfNonAnonyme,
)
from transcripts_pdf.service import Locuteur, ServicePreparationTranscript
from validation_transcript.service import ServiceValidationTranscript

routeur = APIRouter()
_EXECUTEUR = ThreadPoolExecutor(max_workers=2)
_EXECUTEUR_PREPARATION = ThreadPoolExecutor(max_workers=1)
_PREPARATIONS: dict[str, dict] = {}
_TTL_PREPARATION = timedelta(minutes=30)
_PROMPT = Path(__file__).parent.parent / "prompts"
_PROMPT_VALIDATION = (_PROMPT / "validation_transcript.md").read_text()


class LocuteurBody(BaseModel):
    identifiant: str
    role: Literal["interne", "externe", "indetermine"]
    justification: str


class SourcePdfBody(BaseModel):
    type_source: Literal["produit", "bizdev"]
    nom_source: str
    produit_id: int
    projet_id: int | None = None
    date_entretien: date | None
    contenu: str
    contexte: str = ""
    locuteurs: list[LocuteurBody]


def fabrique_depot_transcripts_pdf() -> DepotTranscriptsPdf:
    return DepotTranscriptsPdfPostgres(charge_configuration().base_de_donnees)


def fabrique_service_preparation_pdf() -> ServicePreparationTranscript:
    return ServicePreparationTranscript(
        AdaptateurAlbertReel(charge_configuration().albert),
        (_PROMPT / "anonymisation_transcript.md").read_text(),
    )


def fabrique_service_validation_pdf() -> ServiceValidationTranscript:
    return ServiceValidationTranscript(
        AdaptateurAlbertReel(charge_configuration().albert), _PROMPT_VALIDATION
    )


def fabrique_service_analyse_pdf() -> ServiceAnalysePdf:
    return ServiceAnalysePdf(
        AdaptateurAlbertReel(charge_configuration().albert),
        {
            "produit": (_PROMPT / "analyse_transcript_produit.md").read_text(),
            "bizdev": (_PROMPT / "analyse_transcript_bizdev.md").read_text(),
        },
    )


def fabrique_service_transcripts_pdf(
    depot: DepotTranscriptsPdf = Depends(fabrique_depot_transcripts_pdf),
    garde_fou: ServiceValidationTranscript = Depends(fabrique_service_validation_pdf),
    analyseur: ServiceAnalysePdf = Depends(fabrique_service_analyse_pdf),
) -> ServiceTranscriptsPdf:
    return ServiceTranscriptsPdf(
        depot, garde_fou, analyseur, charge_configuration().albert.delai_transcripts
    )


def fabrique_executeur() -> Executor:
    return _EXECUTEUR


@routeur.post("/transcripts-pdf/preparation", status_code=202)
async def preparer(
    type_source: Literal["produit", "bizdev"] = Form(),
    contexte: str = Form(""),
    fichier: UploadFile = File(),
    service: ServicePreparationTranscript = Depends(fabrique_service_preparation_pdf),
) -> dict:
    _nettoyer_preparations()
    if (
        sum(
            preparation["statut"] == "en_cours"
            for preparation in _PREPARATIONS.values()
        )
        >= 2
    ):
        raise HTTPException(status_code=429, detail="Trop de préparations en cours.")
    contenu = await fichier.read(TAILLE_MAXIMALE + 1)
    jeton = uuid4().hex
    _PREPARATIONS[jeton] = {
        "statut": "en_cours",
        "expire": datetime.now(timezone.utc) + _TTL_PREPARATION,
    }
    _EXECUTEUR_PREPARATION.submit(
        _executer_preparation,
        jeton,
        service,
        fichier.filename or "transcript.pdf",
        contenu,
        type_source,
        contexte,
    )
    return {"jeton": jeton, "statut": "en_cours"}


@routeur.get("/transcripts-pdf/preparation/{jeton}")
def obtenir_preparation(jeton: str) -> dict:
    _nettoyer_preparations()
    preparation = _PREPARATIONS.get(jeton)
    if preparation is None:
        raise HTTPException(
            status_code=404, detail="Préparation expirée ou introuvable."
        )
    if preparation["statut"] == "echec":
        return {"statut": "echec", "erreur": preparation["erreur"]}
    if preparation["statut"] == "termine":
        return {"statut": "termine", **preparation["resultat"]}
    return {"statut": "en_cours"}


def _executer_preparation(
    jeton: str,
    service: ServicePreparationTranscript,
    nom_fichier: str,
    fichier: bytes,
    type_source: str,
    contexte: str,
) -> None:
    try:
        preparation = service.preparer(nom_fichier, fichier, type_source, contexte)
        resultat = {
            "type_source": preparation.type_source,
            "nom_source": preparation.nom_source,
            "date_entretien": preparation.date_entretien,
            "contenu": preparation.contenu,
            "contexte": preparation.contexte,
            "locuteurs": [locuteur._asdict() for locuteur in preparation.locuteurs],
            "remplacements": [
                remplacement._asdict() for remplacement in preparation.remplacements
            ],
        }
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton].update(statut="termine", resultat=resultat)
    except ErreurPdf as erreur:
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton].update(statut="echec", erreur=str(erreur))
    except Exception:
        if jeton in _PREPARATIONS:
            _PREPARATIONS[jeton].update(
                statut="echec", erreur="La préparation du transcript a échoué."
            )


def _nettoyer_preparations() -> None:
    maintenant = datetime.now(timezone.utc)
    for jeton in [
        jeton
        for jeton, valeur in _PREPARATIONS.items()
        if valeur["expire"] <= maintenant
    ]:
        del _PREPARATIONS[jeton]


@routeur.post("/transcripts-pdf", status_code=201)
def confirmer(
    body: SourcePdfBody,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    try:
        source = service.confirmer(
            body.type_source,
            body.nom_source,
            body.produit_id,
            body.projet_id,
            body.date_entretien,
            body.contenu,
            body.contexte,
            [Locuteur(**locuteur.model_dump()) for locuteur in body.locuteurs],
        )
    except SourcePdfNonAnonyme as erreur:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Anonymisez les données signalées avant de confirmer.",
                "problemes": erreur.problemes,
            },
        ) from erreur
    except SourcePdfInvalide as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    return source._asdict()


@routeur.get("/transcripts-pdf/produits/{produit_id}")
def lister(
    produit_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> list[dict]:
    return [_source_dict(source) for source in service.lister(produit_id)]


@routeur.get("/transcripts-pdf/{transcript_id}")
def obtenir(
    transcript_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    source = service.obtenir(transcript_id)
    if source is None:
        raise HTTPException(status_code=404)
    return _source_dict(source)


@routeur.put("/transcripts-pdf/{transcript_id}")
def modifier(
    transcript_id: int,
    body: SourcePdfBody,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    source = service.obtenir(transcript_id)
    if (
        source is None
        or source.type_source != body.type_source
        or source.produit_id != body.produit_id
        or source.projet_id != body.projet_id
    ):
        raise HTTPException(status_code=404)
    try:
        modifie = service.modifier(
            transcript_id,
            body.date_entretien,
            body.contenu,
            body.contexte,
            [Locuteur(**locuteur.model_dump()) for locuteur in body.locuteurs],
        )
    except SourcePdfNonAnonyme as erreur:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Anonymisez les données signalées avant de confirmer.",
                "problemes": erreur.problemes,
            },
        ) from erreur
    except SourcePdfInvalide as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    if modifie is None:
        raise HTTPException(status_code=404)
    return _source_dict(modifie)


@routeur.delete("/transcripts-pdf/{transcript_id}", status_code=204)
def supprimer(
    transcript_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> None:
    if not service.supprimer(transcript_id):
        raise HTTPException(status_code=404)


@routeur.post("/transcripts-pdf/{transcript_id}/analyse", status_code=202)
def analyser(
    transcript_id: int,
    relancer: bool = False,
    executeur: Executor = Depends(fabrique_executeur),
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict:
    try:
        resultat = service.demarrer_analyse(transcript_id, relancer)
    except SourcePdfInvalide as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    if resultat.analyse is None and resultat.job.statut in {"attente", "en_cours"}:
        executeur.submit(_executer_job, resultat.job.id)
    return {"job": _job_dict(resultat.job), "analyse": _analyse_dict(resultat.analyse)}


@routeur.get("/transcripts-pdf/{transcript_id}/analyse")
def obtenir_analyse(
    transcript_id: int,
    service: ServiceTranscriptsPdf = Depends(fabrique_service_transcripts_pdf),
) -> dict | None:
    return _analyse_dict(service.obtenir_analyse(transcript_id))


@routeur.get("/transcripts-pdf/{transcript_id}/job")
def obtenir_job(
    transcript_id: int,
    depot: DepotTranscriptsPdf = Depends(fabrique_depot_transcripts_pdf),
) -> dict:
    job = depot.obtenir_job(transcript_id)
    if job is None:
        raise HTTPException(status_code=404)
    return _job_dict(job)


def reprendre_jobs(
    depot: DepotTranscriptsPdf | None = None, executeur: Executor | None = None
) -> None:
    depot = depot or fabrique_depot_transcripts_pdf()
    executeur = executeur or _EXECUTEUR
    for job_id in depot.lister_jobs_a_reprendre():
        executeur.submit(_executer_job, job_id)


async def surveille_jobs(
    arreter: asyncio.Event,
    scanner: Callable[[], None] = reprendre_jobs,
    intervalle: float = 30,
) -> None:
    while not arreter.is_set():
        await asyncio.to_thread(scanner)
        try:
            await asyncio.wait_for(arreter.wait(), intervalle)
        except TimeoutError:
            pass


def _executer_job(job_id: int, service: ServiceTranscriptsPdf | None = None) -> None:
    (service or fabrique_service_transcripts_pdf()).executer_job(job_id)


def _source_dict(source: SourceTranscriptPdf) -> dict:
    return source._asdict()


def _job_dict(job: JobAnalyseTranscript) -> dict:
    return job._replace(jeton=None)._asdict()


def _analyse_dict(analyse: AnalyseTranscriptPdf | None) -> dict | None:
    return analyse._asdict() if analyse is not None else None
