from fastapi import APIRouter, HTTPException

from api.liste_blanche import routeur as routeur_liste_blanche
from api.liste_noire import routeur as routeur_liste_noire
from api.produits import routeur as routeur_produits
from api.transcripts_pdf import routeur as routeur_transcripts_pdf
from configuration import charge_configuration
from infra.connexion_base_de_donnees import base_de_donnees_est_disponible

routeur = APIRouter()
routeur.include_router(routeur_produits)
routeur.include_router(routeur_liste_blanche)
routeur.include_router(routeur_liste_noire)
routeur.include_router(routeur_transcripts_pdf)


@routeur.get("/sante")
def sante() -> dict[str, str]:
    if not base_de_donnees_est_disponible(charge_configuration().base_de_donnees):
        raise HTTPException(status_code=503, detail="Base de données indisponible")
    return {"statut": "ok"}
