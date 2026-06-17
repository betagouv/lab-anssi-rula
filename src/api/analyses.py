from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from adaptateurs.albert import AdaptateurAlbertReel
from analyses.depot import DepotAnalysesTranscripts
from analyses.service import AnalyseDejaExistante, ServiceAnalyse
from api.transcripts import fabrique_depot_transcripts
from configuration import charge_configuration
from infra.postgres.depot_analyses_transcripts import DepotAnalysesTranscriptsPostgres
from transcripts.depot import DepotTranscripts

_systeme_prompt = (Path(__file__).parent.parent / "prompts" / "analyse_transcript.md").read_text()

routeur = APIRouter()


def fabrique_depot_analyses() -> DepotAnalysesTranscripts:  # pragma: no cover
    return DepotAnalysesTranscriptsPostgres(charge_configuration().base_de_donnees)


def fabrique_service_analyse(
    depot_transcripts: DepotTranscripts = Depends(fabrique_depot_transcripts),
    depot_analyses: DepotAnalysesTranscripts = Depends(fabrique_depot_analyses),
) -> ServiceAnalyse:  # pragma: no cover
    return ServiceAnalyse(
        depot_transcripts=depot_transcripts,
        depot_analyses=depot_analyses,
        albert=AdaptateurAlbertReel(charge_configuration().albert),
        systeme_prompt=_systeme_prompt,
    )


@routeur.post("/analyses/transcripts/{transcript_id}", status_code=201)
def analyser(transcript_id: int, service: ServiceAnalyse = Depends(fabrique_service_analyse)) -> dict:
    try:
        return service.analyser(transcript_id)._asdict()
    except ValueError:
        raise HTTPException(status_code=404)
    except AnalyseDejaExistante:
        raise HTTPException(status_code=409)


@routeur.get("/analyses/transcripts/{transcript_id}")
def obtenir_analyse(transcript_id: int, service: ServiceAnalyse = Depends(fabrique_service_analyse)) -> dict:
    analyse = service.obtenir(transcript_id)
    if analyse is None:
        raise HTTPException(status_code=404)
    return analyse._asdict()


@routeur.get("/analyses")
def lister_analyses(service: ServiceAnalyse = Depends(fabrique_service_analyse)) -> list[dict]:
    return [a._asdict() for a in service.lister()]
