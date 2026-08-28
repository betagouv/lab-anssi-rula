from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from adaptateurs.albert import AdaptateurAlbertReel
from api.fonctionnalites import fabrique_depot_fonctionnalites, fabrique_service_fonctionnalites
from api.idees import fabrique_depot_idees
from api.retours_bizdev import fabrique_depot_retours_bizdev
from api.transcripts import fabrique_depot_transcripts
from besoins.dependances import DependancesBesoins
from besoins.depot import DepotBesoinsDetectes
from besoins.service import ServiceBesoinsDetectes, SourceBesoinInconnue
from configuration import charge_configuration
from fonctionnalites.depot import DepotFonctionnalitesTranscripts
from fonctionnalites.service import ServiceFonctionnalites
from idees.depot import DepotIdees
from infra.postgres.depot_besoins_detectes import DepotBesoinsDetectesPostgres
from retours_bizdev.depot import DepotRetoursBizDev
from transcripts.depot import DepotTranscripts

_prompts = Path(__file__).parent.parent / "prompts"
_prompt_featurebase = (_prompts / "besoin_featurebase.md").read_text()
_prompt_bizdev = (_prompts / "besoin_bizdev.md").read_text()

routeur = APIRouter()


def fabrique_depot_besoins() -> DepotBesoinsDetectes:  # pragma: no cover
    return DepotBesoinsDetectesPostgres(charge_configuration().base_de_donnees)


def fabrique_dependances_besoins(
    depot: DepotBesoinsDetectes = Depends(fabrique_depot_besoins),
    depot_transcripts: DepotTranscripts = Depends(fabrique_depot_transcripts),
    depot_fonctionnalites: DepotFonctionnalitesTranscripts = Depends(fabrique_depot_fonctionnalites),
    service_fonctionnalites: ServiceFonctionnalites = Depends(fabrique_service_fonctionnalites),
    depot_idees: DepotIdees = Depends(fabrique_depot_idees),
    depot_retours: DepotRetoursBizDev = Depends(fabrique_depot_retours_bizdev),
) -> DependancesBesoins:  # pragma: no cover
    return DependancesBesoins(
        depot=depot,
        depot_transcripts=depot_transcripts,
        depot_fonctionnalites=depot_fonctionnalites,
        service_fonctionnalites=service_fonctionnalites,
        depot_idees=depot_idees,
        depot_retours=depot_retours,
    )


def fabrique_service_besoins(
    dependances: DependancesBesoins = Depends(fabrique_dependances_besoins),
) -> ServiceBesoinsDetectes:  # pragma: no cover
    config = charge_configuration()
    return ServiceBesoinsDetectes(
        dependances=dependances,
        albert=AdaptateurAlbertReel(config.albert),
        prompts=(_prompt_featurebase, _prompt_bizdev),
    )


@routeur.get("/besoins")
def lister_besoins(source: str | None = None, produit_id: int | None = None, service: ServiceBesoinsDetectes = Depends(fabrique_service_besoins)) -> list[dict]:
    if source not in {None, "transcript", "idee", "retour_bizdev"}:
        raise HTTPException(status_code=400, detail=f"Source inconnue : {source}")
    return [besoin._asdict() for besoin in service.lister(source, produit_id)]


@routeur.post("/besoins/analyser/{source}")
def analyser_besoins(source: str, produit_id: int | None = None, service: ServiceBesoinsDetectes = Depends(fabrique_service_besoins)) -> list[dict]:
    try:
        return [besoin._asdict() for besoin in service.analyser(source, produit_id)]
    except SourceBesoinInconnue:
        raise HTTPException(status_code=400, detail=f"Source inconnue : {source}")
