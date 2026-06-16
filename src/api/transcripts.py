from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from configuration import charge_configuration
from infra.postgres.depot_transcripts import DepotTranscriptsPostgres
from transcripts.depot import DepotTranscripts


def fabrique_depot_transcripts() -> DepotTranscripts:  # pragma: no cover
    return DepotTranscriptsPostgres(charge_configuration().base_de_donnees)


class NouveauTranscript(BaseModel):
    identite_id: int
    produit_id: int
    date_entretien: date
    contenu: str


routeur = APIRouter()


@routeur.get("/transcripts")
def lister(depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> list[dict]:
    return [t._asdict() for t in depot.lister()]


@routeur.post("/transcripts", status_code=201)
def ajouter(body: NouveauTranscript, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> dict:
    return depot.ajouter(body.identite_id, body.produit_id, body.date_entretien, body.contenu)._asdict()
