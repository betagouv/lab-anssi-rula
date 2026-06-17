from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from adaptateurs.albert import AdaptateurAlbertReel
from api.transcripts import fabrique_depot_transcripts
from configuration import charge_configuration
from fonctionnalites.depot import DepotFonctionnalitesTranscripts
from fonctionnalites.service import FonctionnalitesDejaExistantes, ServiceFonctionnalites
from infra.postgres.depot_fonctionnalites_transcripts import DepotFonctionnalitesTranscriptsPostgres
from transcripts.depot import DepotTranscripts

_systeme_prompt = (Path(__file__).parent.parent / "prompts" / "fonctionnalites_transcript.md").read_text()

routeur = APIRouter()


def fabrique_depot_fonctionnalites() -> DepotFonctionnalitesTranscripts:  # pragma: no cover
    return DepotFonctionnalitesTranscriptsPostgres(charge_configuration().base_de_donnees)


def fabrique_service_fonctionnalites(
    depot_transcripts: DepotTranscripts = Depends(fabrique_depot_transcripts),
    depot_fonctionnalites: DepotFonctionnalitesTranscripts = Depends(fabrique_depot_fonctionnalites),
) -> ServiceFonctionnalites:  # pragma: no cover
    return ServiceFonctionnalites(
        depot_transcripts=depot_transcripts,
        depot_fonctionnalites=depot_fonctionnalites,
        albert=AdaptateurAlbertReel(charge_configuration().albert),
        systeme_prompt=_systeme_prompt,
    )


@routeur.post("/fonctionnalites/transcripts/{transcript_id}", status_code=201)
def calculer(transcript_id: int, service: ServiceFonctionnalites = Depends(fabrique_service_fonctionnalites)) -> list[dict]:
    try:
        return [f._asdict() for f in service.calculer(transcript_id)]
    except ValueError:
        raise HTTPException(status_code=404)
    except FonctionnalitesDejaExistantes:
        raise HTTPException(status_code=409)


@routeur.get("/fonctionnalites/transcripts/{transcript_id}")
def obtenir_fonctionnalites(transcript_id: int, service: ServiceFonctionnalites = Depends(fabrique_service_fonctionnalites)) -> list[dict]:
    fonctionnalites = service.obtenir(transcript_id)
    if not fonctionnalites:
        raise HTTPException(status_code=404)
    return [f._asdict() for f in fonctionnalites]


@routeur.get("/fonctionnalites")
def lister_fonctionnalites(service: ServiceFonctionnalites = Depends(fabrique_service_fonctionnalites)) -> list[dict]:
    return [f._asdict() for f in service.lister()]
