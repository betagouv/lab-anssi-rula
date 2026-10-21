from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

from api.transcripts_pdf import _verifier_origine
from configuration import charge_configuration
from infra.postgres.depot_liste_blanche import DepotListeBlanchePostgres
from liste_blanche.depot import RevisionObsolete, TermeAbsent, TermeDejaPresent
from liste_blanche.service import ServiceListeBlanche

routeur = APIRouter()


def fabrique_service_liste_blanche() -> ServiceListeBlanche:
    return ServiceListeBlanche(
        DepotListeBlanchePostgres(charge_configuration().base_de_donnees)
    )


class TermeBody(BaseModel):
    terme: str = Field(max_length=120)


class ModificationTermeBody(TermeBody):
    revision: int = Field(gt=0)


@routeur.get("/liste-blanche")
def lister(
    service: ServiceListeBlanche = Depends(fabrique_service_liste_blanche),
) -> list[dict]:
    return [terme._asdict() for terme in service.lister()]


@routeur.post("/liste-blanche", status_code=201)
def ajouter(
    body: TermeBody,
    request: Request,
    service: ServiceListeBlanche = Depends(fabrique_service_liste_blanche),
) -> dict:
    _verifier_origine(request)
    try:
        return service.ajouter(body.terme)._asdict()
    except ValueError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    except TermeDejaPresent as erreur:
        raise HTTPException(status_code=409, detail="Ce terme existe déjà.") from erreur


@routeur.put("/liste-blanche/{identifiant}")
def modifier(
    body: ModificationTermeBody,
    request: Request,
    identifiant: int = Path(gt=0),
    service: ServiceListeBlanche = Depends(fabrique_service_liste_blanche),
) -> dict:
    _verifier_origine(request)
    try:
        return service.modifier(identifiant, body.terme, body.revision)._asdict()
    except ValueError as erreur:
        raise HTTPException(status_code=422, detail=str(erreur)) from erreur
    except TermeDejaPresent as erreur:
        raise HTTPException(status_code=409, detail="Ce terme existe déjà.") from erreur
    except RevisionObsolete as erreur:
        raise HTTPException(
            status_code=409, detail="La liste a été modifiée."
        ) from erreur
    except TermeAbsent as erreur:
        raise HTTPException(status_code=404, detail="Terme introuvable.") from erreur


@routeur.delete("/liste-blanche/{identifiant}", status_code=204)
def supprimer(
    request: Request,
    identifiant: int = Path(gt=0),
    revision: int = Query(gt=0),
    service: ServiceListeBlanche = Depends(fabrique_service_liste_blanche),
) -> None:
    _verifier_origine(request)
    try:
        service.supprimer(identifiant, revision)
    except RevisionObsolete as erreur:
        raise HTTPException(
            status_code=409, detail="La liste a été modifiée."
        ) from erreur
    except TermeAbsent as erreur:
        raise HTTPException(status_code=404, detail="Terme introuvable.") from erreur
