from fastapi import APIRouter

from api.identites import routeur as routeur_identites
from api.produits import routeur as routeur_produits
from api.transcripts import routeur as routeur_transcripts

routeur = APIRouter()

routeur.include_router(routeur_identites)
routeur.include_router(routeur_produits)
routeur.include_router(routeur_transcripts)


@routeur.get("/sante")
def sante() -> dict[str, str]:
    return {"statut": "ok"}
