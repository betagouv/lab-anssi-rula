from datetime import date

from fastapi import APIRouter, Depends, HTTPException
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


@routeur.get("/transcripts/{id}")
def obtenir(id: int, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> dict:
    transcript = depot.obtenir(id)
    if transcript is None:
        raise HTTPException(status_code=404)
    return transcript._asdict()


@routeur.put("/transcripts/{id}")
def modifier(id: int, body: NouveauTranscript, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> dict:
    transcript = depot.modifier(id, body.identite_id, body.produit_id, body.date_entretien, body.contenu)
    if transcript is None:
        raise HTTPException(status_code=404)
    return transcript._asdict()


@routeur.delete("/transcripts/{id}", status_code=204)
def supprimer(id: int, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> None:
    if not depot.supprimer(id):
        raise HTTPException(status_code=404)
