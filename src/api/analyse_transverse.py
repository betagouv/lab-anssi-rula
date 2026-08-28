from fastapi import APIRouter, Depends, HTTPException

from api.besoins import fabrique_service_besoins
from api.correspondances import en_dict, fabrique_service_correspondance
from api.produits import fabrique_depot_produits
from besoins.service import ServiceBesoinsDetectes
from correspondance.service import ServiceCorrespondance
from produits.depot import DepotProduits

routeur = APIRouter()


def _verifier_produit(produit_id: int, produits: DepotProduits) -> None:
    if not any(produit.id == produit_id for produit in produits.lister()):
        raise HTTPException(status_code=404, detail="Produit introuvable.")


def _charger(
    produit_id: int,
    besoins: ServiceBesoinsDetectes,
    correspondances: ServiceCorrespondance,
) -> dict:
    return {
        "besoins": [besoin._asdict() for besoin in besoins.lister(produit_id=produit_id)],
        "correspondances": en_dict(correspondances.charger(produit_id)),
        "calcule_le": correspondances.dernier_calcul(produit_id),
    }


@routeur.get("/produits/{produit_id}/analyse-transverse")
def charger(
    produit_id: int,
    produits: DepotProduits = Depends(fabrique_depot_produits),
    besoins: ServiceBesoinsDetectes = Depends(fabrique_service_besoins),
    correspondances: ServiceCorrespondance = Depends(fabrique_service_correspondance),
) -> dict:
    _verifier_produit(produit_id, produits)
    return _charger(produit_id, besoins, correspondances)


@routeur.post("/produits/{produit_id}/analyse-transverse")
def analyser(
    produit_id: int,
    produits: DepotProduits = Depends(fabrique_depot_produits),
    besoins: ServiceBesoinsDetectes = Depends(fabrique_service_besoins),
    correspondances: ServiceCorrespondance = Depends(fabrique_service_correspondance),
) -> dict:
    _verifier_produit(produit_id, produits)
    anciens = besoins.lister(produit_id=produit_id)
    try:
        prepares = {
            source: besoins.preparer(source, produit_id)
            for source in ("transcript", "idee", "retour_bizdev")
        }
        for source, elements in prepares.items():
            besoins.remplacer(source, elements, produit_id)
        correspondances.analyser(produit_id)
    except Exception:
        besoins.restaurer(anciens, produit_id)
        raise
    return _charger(produit_id, besoins, correspondances)


@routeur.get("/produits/{produit_id}/besoins")
def lister_besoins(
    produit_id: int,
    produits: DepotProduits = Depends(fabrique_depot_produits),
    besoins: ServiceBesoinsDetectes = Depends(fabrique_service_besoins),
) -> list[dict]:
    _verifier_produit(produit_id, produits)
    return [besoin._asdict() for besoin in besoins.lister(produit_id=produit_id)]
