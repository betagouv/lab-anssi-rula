from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from adaptateurs.albert import AdaptateurAlbertReel
from api.identites import fabrique_depot_identites
from api.produits import fabrique_depot_produits
from configuration import charge_configuration
from identites.depot import DepotIdentites
from infra.postgres.depot_transcripts import DepotTranscriptsPostgres
from produits.depot import DepotProduits
from transcripts.depot import DepotTranscripts
from validation_transcript.service import ServiceValidationTranscript


def fabrique_depot_transcripts() -> DepotTranscripts:  # pragma: no cover
    return DepotTranscriptsPostgres(charge_configuration().base_de_donnees)


_systeme_prompt = (
    Path(__file__).parent.parent / "prompts" / "validation_transcript.md"
).read_text()


def fabrique_service_validation_transcript() -> ServiceValidationTranscript:
    return ServiceValidationTranscript(
        AdaptateurAlbertReel(charge_configuration().albert), _systeme_prompt
    )


class NouveauTranscript(BaseModel):
    identite_id: int | None = None
    nouvelle_identite: str | None = None
    produit_id: int | None = None
    nouveau_produit: str | None = None
    date_entretien: date
    contenu: str


routeur = APIRouter()


@routeur.get("/transcripts")
def lister(depot: DepotTranscripts = Depends(fabrique_depot_transcripts)) -> list[dict]:
    return [t._asdict() for t in depot.lister()]


@routeur.post("/transcripts", status_code=201)
def ajouter(
    body: NouveauTranscript,
    depot: DepotTranscripts = Depends(fabrique_depot_transcripts),
    depot_identites: DepotIdentites = Depends(fabrique_depot_identites),
    depot_produits: DepotProduits = Depends(fabrique_depot_produits),
    service: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
) -> dict:
    _verifier(body, service)
    return depot.ajouter(
        _id_ressource(body.identite_id, body.nouvelle_identite, depot_identites),
        _id_ressource(body.produit_id, body.nouveau_produit, depot_produits),
        body.date_entretien,
        body.contenu,
    )._asdict()


@routeur.get("/transcripts/{id}")
def obtenir(
    id: int, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)
) -> dict:
    transcript = depot.obtenir(id)
    if transcript is None:
        raise HTTPException(status_code=404)
    return transcript._asdict()


@routeur.put("/transcripts/{id}")
def modifier(
    id: int,
    body: NouveauTranscript,
    depot: DepotTranscripts = Depends(fabrique_depot_transcripts),
    depot_identites: DepotIdentites = Depends(fabrique_depot_identites),
    depot_produits: DepotProduits = Depends(fabrique_depot_produits),
    service: ServiceValidationTranscript = Depends(
        fabrique_service_validation_transcript
    ),
) -> dict:
    _verifier(body, service)
    transcript = depot.modifier(
        id,
        _id_ressource(body.identite_id, body.nouvelle_identite, depot_identites),
        _id_ressource(body.produit_id, body.nouveau_produit, depot_produits),
        body.date_entretien,
        body.contenu,
    )
    if transcript is None:
        raise HTTPException(status_code=404)
    return transcript._asdict()


@routeur.delete("/transcripts/{id}", status_code=204)
def supprimer(
    id: int, depot: DepotTranscripts = Depends(fabrique_depot_transcripts)
) -> None:
    if not depot.supprimer(id):
        raise HTTPException(status_code=404)


def _id_ressource(
    id: int | None,
    nouveau_nom: str | None,
    depot: DepotIdentites | DepotProduits,
) -> int:
    if id is not None and nouveau_nom is None:
        return id
    if id is None and nouveau_nom:
        return depot.ajouter(nouveau_nom).id
    raise HTTPException(
        status_code=422,
        detail="Une identité ou un projet doit être sélectionné ou créé.",
    )


def _verifier(body: NouveauTranscript, service: ServiceValidationTranscript) -> None:
    try:
        validation = service.valider(body.contenu)
    except Exception as erreur:
        raise HTTPException(
            status_code=503,
            detail="La vérification des données est indisponible. Le transcript n'a pas été enregistré.",
        ) from erreur
    if not validation.valide:
        raise HTTPException(
            status_code=422,
            detail={
                "raisons": [probleme._asdict() for probleme in validation.problemes]
            },
        )
