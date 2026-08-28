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


def _passage(besoin, membre=None) -> dict:
    source = membre.source if membre else besoin.source
    source_id = (
        membre.source_id
        if membre and membre.source_id is not None
        else besoin.source_id
    )
    texte = besoin.nom_generique if besoin else membre.texte
    verbatim = (
        (
            besoin.verbatim
            or (membre.verbatim if membre else None)
            or besoin.texte_original
        )
        if besoin
        else (membre.verbatim or membre.texte)
    )
    transcript_id = besoin.transcript_id if besoin else membre.transcript_id
    projet_id = getattr(besoin, "projet_id", None) if besoin else None
    return {
        "source": source,
        "source_id": source_id,
        "transcript_id": transcript_id,
        "projet_id": projet_id,
        "texte_normalise": texte,
        "verbatim": verbatim,
    }


def _groupes(besoins: list, clusters: list) -> list[dict]:
    index = {(besoin.source, besoin.source_id): besoin for besoin in besoins}
    inclus: set[tuple[str, int]] = set()
    groupes = []
    for cluster in clusters:
        passages = []
        for membre in cluster.membres:
            source_id = membre.source_id
            besoin = (
                index.get((membre.source, source_id)) if source_id is not None else None
            )
            passages.append(_passage(besoin, membre))
            if source_id is not None:
                inclus.add((membre.source, source_id))
        if passages:
            groupes.append(
                {
                    "nom_generique": cluster.libelle,
                    "occurrences": len(passages),
                    "passages": passages,
                }
            )
    for besoin in besoins:
        if (besoin.source, besoin.source_id) not in inclus:
            groupes.append(
                {
                    "nom_generique": besoin.nom_generique,
                    "occurrences": 1,
                    "passages": [_passage(besoin)],
                }
            )
    return groupes


def _charger(
    produit_id: int,
    besoins: ServiceBesoinsDetectes,
    correspondances: ServiceCorrespondance,
) -> dict:
    besoins_liste = besoins.lister(produit_id=produit_id)
    clusters = correspondances.charger(produit_id)
    return {
        "besoins": [besoin._asdict() for besoin in besoins_liste],
        "correspondances": en_dict(clusters),
        "groupes": _groupes(besoins_liste, clusters),
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
