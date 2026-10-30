from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

from api.transcripts_pdf import _verifier_origine
from termes_liste import (
    CouleurListe,
    RevisionObsolete,
    ServiceListeTermes,
    TermeAbsent,
    TermeDejaPresent,
)


class TermeBody(BaseModel):
    terme: str = Field(max_length=120)


class ModificationTermeBody(TermeBody):
    revision: int = Field(gt=0)


def creer_routeur_liste(
    couleur: CouleurListe, fabrique_service: Callable[[], ServiceListeTermes]
) -> APIRouter:
    routeur = APIRouter()
    chemin = f"/liste-{couleur}"

    @routeur.get(chemin)
    def lister(service: ServiceListeTermes = Depends(fabrique_service)) -> list[dict]:
        return [terme._asdict() for terme in service.lister()]

    @routeur.post(chemin, status_code=201)
    def ajouter(
        body: TermeBody,
        request: Request,
        service: ServiceListeTermes = Depends(fabrique_service),
    ) -> dict:
        _verifier_origine(request)
        try:
            return service.ajouter(body.terme)._asdict()
        except ValueError as erreur:
            raise HTTPException(status_code=422, detail=str(erreur)) from erreur
        except TermeDejaPresent as erreur:
            raise HTTPException(
                status_code=409, detail="Ce terme existe déjà."
            ) from erreur

    @routeur.put(f"{chemin}/{{identifiant}}")
    def modifier(
        body: ModificationTermeBody,
        request: Request,
        identifiant: int = Path(gt=0),
        service: ServiceListeTermes = Depends(fabrique_service),
    ) -> dict:
        _verifier_origine(request)
        try:
            return service.modifier(identifiant, body.terme, body.revision)._asdict()
        except ValueError as erreur:
            raise HTTPException(status_code=422, detail=str(erreur)) from erreur
        except TermeDejaPresent as erreur:
            raise HTTPException(
                status_code=409, detail="Ce terme existe déjà."
            ) from erreur
        except RevisionObsolete as erreur:
            raise HTTPException(
                status_code=409, detail="La liste a été modifiée."
            ) from erreur
        except TermeAbsent as erreur:
            raise HTTPException(
                status_code=404, detail="Terme introuvable."
            ) from erreur

    @routeur.delete(f"{chemin}/{{identifiant}}", status_code=204)
    def supprimer(
        request: Request,
        identifiant: int = Path(gt=0),
        revision: int = Query(gt=0),
        service: ServiceListeTermes = Depends(fabrique_service),
    ) -> None:
        _verifier_origine(request)
        try:
            service.supprimer(identifiant, revision)
        except RevisionObsolete as erreur:
            raise HTTPException(
                status_code=409, detail="La liste a été modifiée."
            ) from erreur
        except TermeAbsent as erreur:
            raise HTTPException(
                status_code=404, detail="Terme introuvable."
            ) from erreur

    return routeur
