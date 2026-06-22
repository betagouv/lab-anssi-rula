from fastapi import APIRouter

from api.analyses import routeur as routeur_analyses
from api.correspondances import routeur as routeur_correspondances
from api.fonctionnalites import routeur as routeur_fonctionnalites
from api.idees import routeur as routeur_idees
from api.identites import routeur as routeur_identites
from api.produits import routeur as routeur_produits
from api.retours_bizdev import routeur as routeur_retours_bizdev
from api.transcripts import routeur as routeur_transcripts

routeur = APIRouter()

routeur.include_router(routeur_identites)
routeur.include_router(routeur_produits)
routeur.include_router(routeur_transcripts)
routeur.include_router(routeur_analyses)
routeur.include_router(routeur_fonctionnalites)
routeur.include_router(routeur_idees)
routeur.include_router(routeur_retours_bizdev)
routeur.include_router(routeur_correspondances)


@routeur.get("/sante")
def sante() -> dict[str, str]:
    return {"statut": "ok"}
